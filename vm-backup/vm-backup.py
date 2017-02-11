#!/usr/bin/env python3
#on vps hosts cron will kick off this script to do a zfs snapshot of
#/var/libvirt/images and then snapshot send to recieving freenas box
#add *args to all for testing
#
#zfs pool on kvm hosts/othermachines is hostname 
#pool snapshot will always be hostname@backupDATETIME
#external san/freenas pools will be storage
#so - zfs recv storage/hostname@backupDATETIME
import os
import smtplib
import configparser
import sys
import subprocess
import datetime
import socket
import smtplib
from email.mime.multipart import MIMEMultipart
config = ""
hostname = ""
name = ""

def read_config():
	global config
	try:
		config = configparser.ConfigParser()
		config.read('vm-backup.ini')
	except:
		print('BACKUP FAILED: COULD NOT ACCESS CONFIG FILE')
		sys.exit()

def send_mail(subject,message):
	email= MIMEMultipart()
	email['subject'] = subject
	email['message'] = message
	mail = smtplib.SMTP(host=config['emailserver'],port=config['emailport'])
	mail.login(config['emailuser'],config['emailpassword'], intial_response_ok=True)
	mail.send_message(email,from_addr=config['emailuser'],to_addr=config['emaildest'])


#remove last snapshot
#make a standalone version of this for freenas box but retain snapshots up to a month old
def error_check(err, hostname):
	if len(err) > 1:
		send_mail(hostname+"@Error occured while taking zfs snapshot",err)
		sys.exit()

def clean_output(stdout,stderr):
	out = stdout.decode()
	err = stderr.decode()
	return out,err

def clean_snapshots(hostname, name):
	#use awk to get a pure list of snapshots and remove all except newest
	#zfs list -t snapshot | awk{}
	#zfs destroy snapshot
	proc = subprocess.run("zfs list -t snapshot | awk 'FNR==2{print $1}'",shell=True)
	out, err = clean_output(proc.stout,proc.stderr)
	error_check(err, hostname)
	proc = subprocess.run('zfs destroy {name}'.format(name=name),shell=True)
	out, err = clean_output(proc.stout,proc.stderr)
	error_check(err,hostname)

#pools will be hostnames
def take_snapshot():
	global	name
	now = str(datetime.datetime.now())
	now = now.replace(' ','#')
	name = '{hostname}@backup{now}'.format(hostname=hostname,now=now)
	proc = subprocess.run(['zfs','snapshot',name]
		, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	#returns bytes so use decode() method to get strings
	out, err = clean_output(proc.stout,proc.stderr)
	error_check(err,hostname)


def send_snapshot():
	remotepool = config['remotepool']
	remotehost = config['remotehost']
	remoteuser = config['remoteuser']
	key = config['keyfile']
	proc = subprocess.run('zfs send -i {name} | ssh -i {key} {remoteuser}@{remotehost} zfs recv {remotepool}/{name}'.format(
		name=name,remotepool=remotepool,remotehost=remotehost,remoteuser=remoteuser,key=key),shell=True,
		stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	out, err = clean_output(proc.stout,proc.stderr)
	error_check(err)



def main():
	global hostname
	hostname = socket.gethostname()
	try:
		read_config()
		take_snapshot()
		send_snapshot()
		clean_snapshots()
		send_mail('{hostname} completed backup succesfully'.format(hostname=hostname),'')
	except FileNotFoundError:
		print('zfs not found on system')
		send_mail('zfs not found on {hostname}'.format(hostname=hostname),'')


main()
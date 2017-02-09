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
config = 0
def send_mail(subject,message):

def read_config():
	global config
	try:
		config = configparser.ConfigParser()
		config.read('config')
	except:
		print('BACKUP FAILED: COULD NOT ACCESS CONFIG FILE')
		sys.exit()

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
	hostname = socket.gethostname()
	now = str(datetime.datetime.now())
	now = now.replace(' ','#')
	name = '{hostname}@backup{now}'.format(hostname=hostname,now=now)
	proc = subprocess.run(['zfs','snapshot',name]
		, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	#returns bytes so use decode() method to get strings
	out, err = clean_output(proc.stout,proc.stderr)
	error_check(err,hostname)
	return name , hostname ,now


def send_snapshot(name):
	hostpool = config['hostpool']+name
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
	read_config()
	name, hostname, now = take_snapshot()
	send_snapshot(name, hostname,now)
	clean_snapshots(hostname,name)
	send_mail



#!/usr/bin/env python3
#send emails to alert of over 75% use
#df -h | grep pool-name | awk {'print $5'}
import socket
import subprocess
config = ''

def read_config():
	global config
	try:
		config = configparser.ConfigParser()
		config.read('config')
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

def check_space():
	proc = subprocess.run("df -h | grep {poolname} | awk {'print $5'}".format(poolname=config['poolname']),shell=True)
	out = proc.stdout.decode()
	err = proc.stderr.decode()
	use = int(out.replace('%',''))
	if config >= int(config['space']):
		return 'alert'
	else:
		return 'clear'

def main():
	hostname = socket.gethostname()
	result = check_space()
	if result == 'alert':
		send_mail('{hostname} has exceeded 75% zfs use'.format(hostname=hostname),'Please have a sysadmin look into this')
import os
import requests
import json
import smtplib
import sys
import time

from email.mime.text import MIMEText

API_KEY = os.environ['WUNDERGROUND_API_KEY']
WUNDERGROUND_KEY = os.environ['WUNDERGROUND_KEY']
LONG_LAT = os.environ['LONG_LAT']
EMAIL_ADDRESS = os.environ['WINDOW_EMAIL_ADDRESS']
PASSWORD = os.environ['WINDOW_EMAIL_PASSWORD']
MAIL_SERVER = 'smtp.gmail.com:587'

THRESHOLD = 72
DELTA_THRESHOLD = 0.1
SUBJECT_TAG = "[weather-window] "
NOISY_EMAILS = False
URL = 'http://api.wunderground.com/api/%s/conditions/forecast/q/%s.json' % ( WUNDERGROUND_KEY, LONG_LAT )
INTERVAL = 300

window_closed = None
last_temp = None
was_rising = True

def send_mail(mesg, recipient, subj):
	mesg = MIMEText(mesg)
	mesg['Subject'] = SUBJECT_TAG + subj
	mesg['To'] = recipient

	try:
		s = smtplib.SMTP(MAIL_SERVER)
		s.starttls()
		s.login(EMAIL_ADDRESS, PASSWORD)
		s.sendmail(EMAIL_ADDRESS, recipient, mesg.as_string())
		s.quit()
	except:
		raise

while True:
	be_quiet = False
	current_time = time.localtime()
	timestamp = time.strftime('%H:%M: ', current_time)

	try:
		r = requests.get(URL)
		if r.status_code != 200:
			raise Exception('Bad status code: ' + r.status_code)
		try:
			response = r.json()
		except:
			raise
	except:
		print timestamp + "Unexpected error: " + sys.exc_info()[0]
		time.sleep(INTERVAL)
		continue

	current_temp = float(response['current_observation']['temp_f'])
	if not last_temp:
		last_temp = current_temp
		mesg = "Current temperature is %1.2f." % current_temp
	delta = current_temp - last_temp

	if ( window_closed == None ):
		if ( current_temp > THRESHOLD ):
			print "It's too hot to have the window open."
			window_closed = True
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, "It's hot")
		else:
			print "It's safe to have the window open."
			window_closed = False
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, "It's not that hot")
	elif ( window_closed and ( current_temp < THRESHOLD ) ):
		mesg = "Temperature dropped to %1.2f. Open the window!" % current_temp
		window_closed = False
		send_mail(mesg, EMAIL_ADDRESS, 'Time to open the window!')
	elif ( not window_closed and ( current_temp > THRESHOLD ) ):
		mesg = "Temperature rose to %1.2f. Close the window!" % current_temp
		window_closed = True
		send_mail(mesg, EMAIL_ADDRESS, 'Time to close the window!')
	elif ( delta > DELTA_THRESHOLD ):
		if not was_rising:
			mesg = "WARNING! Temperature has started rising! Currently %1.2f (an increase of %1.2f)." % (current_temp, delta)
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, 'Heat rising!')
		else:
			mesg = "Temperature rose by %1.2f to %1.2f." % (delta, current_temp)
		was_rising = True
	elif ( delta < (DELTA_THRESHOLD * -1) ):
		if was_rising:
			mesg = "Relief is in sight... the temperature has started dropping. Currently %1.2f (a decrease of %1.2f)." % (current_temp, delta * -1)
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, 'Good news!')
		else:
			mesg = "Temperature dropped by %1.2f to %1.2f." % (delta * -1, current_temp)
		was_rising = False
	else:
#		print timestamp + "Delta: %1.2f. Current temp: %1.2f" % (delta, current_temp)
		be_quiet = True

	if not be_quiet:
		mesg = timestamp + mesg
		print mesg

	last_temp = current_temp

	time.sleep(INTERVAL)

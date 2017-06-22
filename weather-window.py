import os
import requests
import json
import smtplib
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

primed = None
last_temp = None
was_rising = True

def send_mail(mesg, recipient, subj):
	mesg = MIMEText(mesg)
	mesg['Subject'] = subj
	mesg['To'] = recipient

	s = smtplib.SMTP(MAIL_SERVER)
	s.starttls()
	s.login(EMAIL_ADDRESS, PASSWORD)
	s.sendmail(EMAIL_ADDRESS, recipient, mesg.as_string())
	s.quit()

while True:
	be_quiet = False

	r = requests.get(URL)

	if r.status_code != 200:
		print "Bad status code: "
		print r.status_code
		time.sleep(300)
		continue

	response = r.json()

	current_temp = float(response['current_observation']['temp_f'])
	current_time = time.localtime()
	if not last_temp:
		last_temp = current_temp
		mesg = "Current temperature is %1.1f." % current_temp
	delta = current_temp - last_temp

	timestamp = time.strftime('%H:%M: ', current_time)

	if ( primed == None ):
		if ( current_temp > THRESHOLD ):
			print "It's too hot to have the window open."
			primed = True
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + "It's hot")
		else:
			print "It's safe to have the window open."
			primed = False
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + "It's not that hot")
	elif ( primed and ( current_temp < THRESHOLD ) ):
		mesg = "Temperature dropped to %1.1f. Open the window!" % current_temp
		primed = False
		send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + 'Time to open the window!')
	elif ( not primed and ( current_temp > THRESHOLD ) ):
		mesg = "Temperature rose to %1.1f. Close the window!" % current_temp
		primed = True
		send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + 'Time to close the window!')
	elif ( delta > DELTA_THRESHOLD ):
		if not was_rising:
			mesg = "WARNING! Temperature has started rising! Currently %1.1f (an increase of %1.1f)." % (current_temp, delta)
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + 'Heat rising!')
		else:
			mesg = "Temperature rose by %1.1f to %1.1f." % (delta, current_temp)
		was_rising = True
	elif ( delta < (DELTA_THRESHOLD * -1) ):
		if was_rising:
			mesg = "Relief is in sight... the temperature has started dropping. Currently %1.1f (a decrease of %1.1f)." % (current_temp, delta * -1)
			if NOISY_EMAILS:
				send_mail(mesg, EMAIL_ADDRESS, SUBJECT_TAG + 'Good news!')
		else:
			mesg = "Temperature dropped by %1.1f to %1.1f." % (delta * -1, current_temp)
		was_rising = False
	else:
#		print timestamp + "Delta: %1.1f. Current temp: %1.1f" % (delta, current_temp)
		be_quiet = True

	if not be_quiet:
		mesg = timestamp + mesg
		print mesg

	last_temp = current_temp

	time.sleep(300)

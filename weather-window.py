import os
import requests
import json
import smtplib
import time

from email.mime.text import MIMEText

api_key = os.environ['WUNDERGROUND_API_KEY']
wunderground_key = os.environ['WUNDERGROUND_KEY']
long_lat = os.environ['LONG_LAT']
email_address = os.environ['WINDOW_EMAIL_ADDRESS']
password = os.environ['WINDOW_EMAIL_PASSWORD']

primed = None
last_temp = None
threshold = 72
subject_tag = "[weather-window] "

url = 'http://api.wunderground.com/api/%s/conditions/forecast/q/%s.json' % ( wunderground_key, long_lat )

def send_mail(mesg, recipient, subj):
    mesg = MIMEText(mesg)
    mesg['Subject'] = subj
    mesg['To'] = recipient

    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login(email_address, password)
    s.sendmail(email_address, recipient, mesg.as_string())
    s.quit()

was_rising = True

while True:
    be_quiet = False

    r = requests.get(url)

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
        if ( current_temp > threshold ):
            print "It's too hot to have the window open."
            primed = True
            send_mail(mesg, email_address, subject_tag + "It's hot")
        else:
            print "It's safe to have the window open."
            primed = False
            send_mail(mesg, email_address, subject_tag + "It's not that hot")
    elif ( primed and ( current_temp < threshold ) ):
        mesg = "Temperature dropped to %1.1f. Open the window!" % current_temp
        primed = False
        send_mail(mesg, email_address, subject_tag + 'Time to open the window!')
    elif ( not primed and ( current_temp > threshold ) ):
        mesg = "Temperature rose to %1.1f. Close the window!" % current_temp
        primed = True
        send_mail(mesg, email_address, subject_tag + 'Time to close the window!')
    elif ( delta > 0.1 ):
        if not was_rising:
            mesg = "WARNING! Temperature has started rising! Currently %1.1f (an increase of %1.1f)." % (current_temp, delta)
            send_mail(mesg, email_address, subject_tag + 'Heat rising!')
        else:
            mesg = "Temperature rose by %1.1f to %1.1f." % (delta, current_temp)
        was_rising = True
    elif ( delta < -0.1 ):
        if was_rising:
            mesg = "Relief is in sight... the temperature has started dropping. Currently %1.1f (a decrease of %1.1f)." % (current_temp, delta * -1)
            send_mail(mesg, email_address, subject_tag + 'Good news!')
        else:
            mesg = "Temperature dropped by %1.1f to %1.1f." % (delta, current_temp)
        was_rising = False
    else:
        print timestamp + "Delta: %1.1f. Current temp: %1.1f" % (delta, current_temp)
#       be_quiet = True

    if not be_quiet:
        mesg = timestamp + mesg
        print mesg

    time.sleep(300)

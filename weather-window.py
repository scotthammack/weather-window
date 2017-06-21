
import requests
import json
import smtplib
import time

from email.mime.text import MIMEText

from secrets import api_key, wunderground_key, long_lat, email_address, password

primed = None
last_temp = None
threshold = 72

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

    timestamp = time.strftime('%H:%M: ', current_time)

    if ( primed == None ):
        if ( current_temp > threshold ):
            print "It's too hot to have the window open."
            primed = True
            send_mail(mesg, email_address, "It's hot")
        else:
            print "It's safe to have the window open."
            primed = False
            send_mail(mesg, email_address, "It's not that hot")
    elif ( primed and ( current_temp > threshold ) ):
        mesg = "Temperature dropped to %1.1f. Open the window!" % current_temp
        primed = False
        send_mail(mesg, email_address, 'Time to open the window!')
    elif ( not primed and ( current_temp > threshold ) ):
        mesg = "Temperature rose to %1.1f. Close the window!" % current_temp
        primed = True
        send_mail(mesg, email_address, 'Time to close the window!')
    elif ( current_temp - last_temp > 0.1 ):
        mesg = "Temperature rose to %1.1f." % current_temp
    elif ( current_temp - last_temp < -0.1 ):
        mesg = "Temperature dropped to %1.1f." % current_temp
    else:
        be_quiet = True

    if not be_quiet:
        mesg = timestamp + mesg
        print mesg

    time.sleep(300)

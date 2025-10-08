import smtplib
import messagingscript

server = smtplib.SMTP( "smtp.gmail.com", 587 )
server.starttls()

#below password should be from Google Account > Security > App Passwords  NOT the password for your google account
server.login( 'jasonvegapi@gmail.com', 'emur hbrf hygw mgdp' )
from_mail = 'jasonvegapi@gmail.com'
#will need to look up the email for each carrier
# https://help.inteliquent.com/sending-emails-to-sms-or-mms
#below is for a Sprint phone number

def sendMessage(body):
    body = str(body)
    to = '7137028877@vtext.com'
    message = ("From: %s\r\n" % from_mail + "To: %s\r\n" % to + "Subject: %s\r\n" % '' + "\r\n" + body)
    server.sendmail(from_mail, to, message)

def PlantsWateringMessage():
    body = 'Plant is being watered'
    sendMessage(body)
    print("ran water script");

def FillWaterBasin():
    body = 'Water basin is empty'
    sendMessage(body)
    print("ran no water script");



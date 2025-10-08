import smtplib

server = smtplib.SMTP( "smtp.gmail.com", 587 )
server.starttls()

#below password should be from Google Account > Security > App Passwords  NOT the password for your google account
server.login( 'jasonvegapi@gmail.com', 'wwbv whus sabb hrpu' )
from_mail = 'jasonvegapi@gmail.com'
#will need to look up the email for each carrier
# https://help.inteliquent.com/sending-emails-to-sms-or-mms
#below is for a Sprint phone number

to = 'jasonvegapi@gmail.com'#'7137028877@vtext.com'
body = '<ALARM>'
message = ("From: %s\r\n" % from_mail + "To: %s\r\n" % to + "Subject: %s\r\n" % '' + "\r\n" + body)
server.sendmail(from_mail, to, message)
print("ran messaging script");



#The above is Python code for a Gmail account to send a text message. The Gmail account does need to go to Manage Google Account>Security> App Passwords and create a
#password. That is the password for the script, NOT the account password 
import imaplib
import email
import os
import time

EMAIL = "mypi.commands@gmail.com"
PASSWORD = "yourpassword"
IMAP_SERVER = "imap.gmail.com"
COMMAND_PHRASE = "WIFI OFF"

def check_mail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, "UNSEEN")
    if result == "OK":
        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            body = msg.get_payload(decode=True).decode(errors="ignore")

            if COMMAND_PHRASE in body.upper():
                print("Command received: turning Wi-Fi OFF")
                os.system("sudo nmcli radio wifi off")

    mail.close()
    mail.logout()

if __name__ == "__main__":
    while True:
        check_mail()
        time.sleep(60)  # check once per minute

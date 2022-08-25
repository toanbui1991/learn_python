import smtplib
from config_v2 import config  
# creates SMTP session
s = smtplib.SMTP('smtp.gmail.com', 587)
  
# start TLS for security
s.starttls()
  
# Authentication with app password
# app password is the concept of authenticate email for a bot which present real user for automation
# go to manage your google account (https://myaccount.google.com/) and then search for app passwords.
# follow the instruction to generate app password for your account and use it to authenticate your personal email
app_password = config.get("email_app_password")
s.login("toanbui1991@gmail.com", app_password)
  
# message to be sent
message = "Message_you_need_to_send"
  
# sending the mail
s.sendmail("toanbui1991@gmail.com", "djangouserone@gmail.com", message)
  
# terminating the session
s.quit()
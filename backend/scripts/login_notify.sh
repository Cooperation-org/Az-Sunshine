#!/bin/bash
# Server Login Notification Script
# Sends email when someone logs into the server via SSH

# Email configuration
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
FROM_EMAIL="emosmwangi@gmail.com"
TO_EMAIL="emosmwangi@gmail.com"
APP_PASSWORD="fvpq voon nlfk kkuh"

# Get login details
LOGIN_USER="$PAM_USER"
LOGIN_IP="$PAM_RHOST"
LOGIN_TIME=$(date '+%Y-%m-%d %H:%M:%S %Z')
HOSTNAME=$(hostname)
SERVER_IP=$(hostname -I | awk '{print $1}')

# Only send for SSH logins (not local console)
if [ "$PAM_TYPE" != "open_session" ]; then
    exit 0
fi

# Create email content
SUBJECT="[SECURITY ALERT] Server Login: $LOGIN_USER on $HOSTNAME"
BODY="SECURITY ALERT - Server Login Detected

Server: $HOSTNAME ($SERVER_IP)
User: $LOGIN_USER
From IP: $LOGIN_IP
Time: $LOGIN_TIME
Service: $PAM_SERVICE

If this was not you, please investigate immediately!

--
Az-Sunshine Security System"

# Send email using Python (more reliable than mailx for Gmail)
python3 << EOF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = "$SMTP_SERVER"
smtp_port = $SMTP_PORT
from_email = "$FROM_EMAIL"
to_email = "$TO_EMAIL"
password = "$APP_PASSWORD".replace(" ", "")

msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = "$SUBJECT"
msg.attach(MIMEText("""$BODY""", 'plain'))

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
except Exception as e:
    # Log error but don't block login
    with open('/var/log/login_notify.log', 'a') as f:
        f.write(f"Email send failed: {e}\n")
EOF

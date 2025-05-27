import requests
import random
import string
import time
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# --- CONFIGURATION ---
BOT_TOKEN = '6894639909:AAHulDY0fYlHbG36ugSmogoONLbeVVMSQ2c'
CPANEL_USER = 'anujxyzs'
CPANEL_PASS = '15f7v:jtA]CKA4'
CPANEL_HOST = 'anyjbots.xyz'  # without https
EMAIL_DOMAIN = 'anujbots.xyz'
EMAIL_PASSWORD = 'anujbots10anuj'

# Dictionary to store user's email info
user_emails = {}
seen_emails = {}

# --- FUNCTION TO CREATE EMAIL ---
def create_email(username):
    email_user = username.lower() + ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    email = f"{email_user}@{EMAIL_DOMAIN}"
    url = f"https://{CPANEL_HOST}:2083/execute/Email/add_pop"
    payload = {
        "email": email_user,
        "domain": EMAIL_DOMAIN,
        "password": EMAIL_PASSWORD,
        "quota": "1024"
    }
    response = requests.get(url, auth=(CPANEL_USER, CPANEL_PASS), params=payload, verify=False)
    return email if response.json().get("status") == 1 else None

# --- FUNCTION TO CHECK EMAIL INBOX ---
def check_inbox(email):
    username, domain = email.split('@')
    url = f"https://{CPANEL_HOST}:2096/3rdparty/roundcube/?_task=mail&_mbox=INBOX"
    session = requests.Session()
    login_url = f"https://{CPANEL_HOST}:2096/3rdparty/roundcube/?_task=login"
    payload = {
        '_user': email,
        '_pass': EMAIL_PASSWORD
    }
    session.post(login_url, data=payload, verify=False)

    inbox_url = f"https://{CPANEL_HOST}:2096/3rdparty/roundcube/?_task=mail&_mbox=INBOX"
    resp = session.get(inbox_url, verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    subjects = soup.find_all('span', class_='subject')
    messages = [s.get_text(strip=True) for s in subjects]
    return messages

# --- COMMAND: /generate ---
def generate(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    email = create_email(str(user_id))
    if email:
        user_emails[user_id] = email
        seen_emails[user_id] = []
        update.message.reply_text(f"Your email has been created:\n\n`{email}`", parse_mode='Markdown')
    else:
        update.message.reply_text("Failed to create email. Please try again.")

# --- CHECK INBOX PERIODICALLY ---
def auto_check_inbox(context: CallbackContext):
    for user_id, email in user_emails.items():
        new_msgs = check_inbox(email)
        old_msgs = seen_emails.get(user_id, [])
        unseen = [msg for msg in new_msgs if msg not in old_msgs]
        if unseen:
            context.bot.send_message(chat_id=user_id, text=f"New messages on `{email}`:\n" + "\n".join(unseen), parse_mode='Markdown')
            seen_emails[user_id] = new_msgs

# --- MAIN ---
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("generate", generate))

    # Job Queue for checking inbox
    jq = updater.job_queue
    jq.run_repeating(auto_check_inbox, interval=30, first=10)  # check every 30 seconds

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

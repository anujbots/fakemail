import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import time
import threading

BOT_TOKEN = '6894639909:AAHulDY0fYlHbG36ugSmogoONLbeVVMSQ2c'
CPANEL_USER = 'anujxyzs'
CPANEL_PASS = '15f7v:jtA]CKA4'
CPANEL_HOST = 'anujbots.xyz'
EMAIL_DOMAIN = 'anujbots.xyz'
EMAIL_PASSWORD = 'anujbots10anuj'

user_emails = {}         # {user_id: email}
shown_messages = {}      # {email: [msg1, msg2...]}


def create_email(username):
    url = f"https://{CPANEL_HOST}:2083/execute/Email/add_pop"
    payload = {
        "email": username,
        "domain": EMAIL_DOMAIN,
        "password": EMAIL_PASSWORD,
        "quota": "1024"
    }
    response = requests.get(url, auth=(CPANEL_USER, CPANEL_PASS), params=payload, verify=False)
    return response.json()


def get_email_messages(email):
    login_url = f"https://{CPANEL_HOST}:2096/3rdparty/roundcube/index.php"
    session = requests.Session()

    # Login to roundcube
    payload = {
        "_user": email,
        "_pass": EMAIL_PASSWORD,
        "_action": "login",
        "_timezone": "auto",
    }
    try:
        login = session.post(login_url, data=payload, verify=False)
        if "Inbox" not in login.text:
            return []

        # Access inbox
        inbox_url = f"https://{CPANEL_HOST}:2096/3rdparty/roundcube/?_task=mail&_mbox=INBOX"
        inbox_page = session.get(inbox_url, verify=False)
        soup = BeautifulSoup(inbox_page.text, "html.parser")
        subjects = soup.select("table#messagelist tbody tr td.subject span")

        messages = []
        for s in subjects:
            subject = s.get_text(strip=True)
            if subject:
                messages.append(subject)

        return messages

    except Exception as e:
        print(f"Fetch error: {e}")
        return []


def generate(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    username = str(user_id)[-6:]  # unique part from Telegram ID
    email = f"{username}@{EMAIL_DOMAIN}"

    res = create_email(username)
    if res.get("status") == 1:
        user_emails[user_id] = email
        shown_messages[email] = []
        update.message.reply_text(f"Email created: `{email}`\nCheck your inbox here via bot.", parse_mode="Markdown")
    else:
        update.message.reply_text(f"Error: {res.get('errors')}")


def check_inbox_loop(bot):
    while True:
        time.sleep(1)
        for user_id, email in user_emails.items():
            msgs = get_email_messages(email)
            for msg in msgs:
                if msg not in shown_messages[email]:
                    bot.send_message(chat_id=user_id, text=f"New email on {email}:\n{msg}")
                    shown_messages[email].append(msg)


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("generate", generate))

    # Start inbox checker thread
    t = threading.Thread(target=check_inbox_loop, args=(updater.bot,), daemon=True)
    t.start()

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

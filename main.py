#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
This script is heavily inspired by the echobot example found on the module's
site. Some parameters should be set in a config.py file next to this one.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import config
import datetime 
from datetime import datetime 
import os, json
from pprint import pprint


from nextcloud import NextCloud
from webdav3.client import Client

EMAIL_FROM = config.EMAIL_FROM
EMAIL_PASSWORD = config.EMAIL_PASSWORD # Use App Password for Gmail
EMAIL_TO = config.EMAIL_TO

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



async def send_email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Getting the messages into a list and sending them in an email."""
    if(update.effective_chat.id==config.chat_id):
        text=[]
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # If the file does not exist, start with an empty dictionary
            await update.message.reply_text(("Nincs üzenet!"))
            return
        logger.info(data)
        for key, value in data.items():
            text.append(value)

        await update.message.reply_text(("Üzenetek elküldve!"))
        send_email(text)
        logger.info("\n"+str(text))
        os.remove('data.json')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if(update.effective_chat.id==config.chat_id):
        await update.message.reply_text("Jaj-jaj")

async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the dict."""
    if(update.effective_chat.id==config.chat_id):
        os.remove('data.json')
        await update.message.reply_text("Az összes üzenet törölve!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handling when a new message or a message edition is sent."""
    message=None
    text=""
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # If the file does not exist, start with an empty dictionary
        data = {}

    if(update.effective_chat.id==config.chat_id):
        if update.message:
            message = update.message
        elif update.edited_message:
            message = update.edited_message
        if message!=None:
            reply_to_message = message.reply_to_message
            if reply_to_message:
                text += ">>"+reply_to_message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+": "+str(reply_to_message.text) + "\n"
            text+=">"+message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+": "+(str(message.text))
            data[message.message_id] = text
            with open('data.json', 'w') as f:
                json.dump(data, f)

async def echo_img(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handling when a messages containing an image or a gif is sent."""
    message=None
    text=""
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # If the file does not exist, start with an empty dictionary
        data = {}

    if(update.effective_chat.id==config.chat_id):
        if update.message:
            message = update.message
        elif update.edited_message:
            message = update.edited_message
        if message!=None:
            reply_to_message = message.reply_to_message
            if reply_to_message:
                text += ">>"+reply_to_message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+": "+str(reply_to_message.text) + "\n"
            text+=">"+message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+": "+config.img_placeholder
            data[message.message_id] = text
            with open('data.json', 'w') as f:
                json.dump(data, f)


# Initialize Nextcloud clients
nc = NextCloud(
    endpoint=config.NEXTCLOUD_URL,
    user=config.NEXTCLOUD_USER,
    password=config.NEXTCLOUD_PASSWORD
)
webdav_options = {
    'webdav_hostname': f"{config.NEXTCLOUD_URL}/remote.php/webdav/",
    'webdav_login': config.NEXTCLOUD_USER,
    'webdav_password': config.NEXTCLOUD_PASSWORD
}
webdav_client = Client(webdav_options)

async def echo_img2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.effective_chat.id == config.chat_id:
            message = update.message
            message_id = message.message_id
            date = message.date

            # Check if the message contains a photo
            if message.photo:
                # Get best quality
                photo_file = await message.photo[-1].get_file()

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_name = f"{timestamp}_{photo_file.file_unique_id}.jpg"
                folder_path = f"telegram_bot_images/{date.strftime('%Y-%m')}"
                full_remote_path = f"{folder_path}/{file_name}"

                # Create temporary directory
                os.makedirs('temp', exist_ok=True)

                # Download photo temporarily
                local_path = f"temp/{file_name}"
                await photo_file.download_to_drive(local_path)

            # Check if the message contains a document
            elif message.document:
                document_file = await message.document.get_file()
                mime_type = message.document.mime_type

                # Determine the file type based on MIME type
                if mime_type.startswith('image/'):
                    file_type = 'image'
                elif mime_type.startswith('video/'):
                    file_type = 'video'
                elif mime_type == 'image/gif':
                    file_type = 'gif'
                else:
                    await update.message.reply_text("A MailerBot nem fogja elküldeni ezt a fájltípust.")
                    return

                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                file_name = f"{timestamp}_{message.document.file_name}"
                folder_path = f"telegram_bot_{file_type}s/{date.strftime('%Y-%m')}"
                full_remote_path = f"{folder_path}/{file_name}"

                # Create temporary directory
                os.makedirs('temp', exist_ok=True)

                # Download document temporarily
                local_path = f"temp/{file_name}"
                await document_file.download_to_drive(local_path)

            else:
                await update.message.reply_text("A MailerBot nem fogja elküldeni ezt a fájltípust.")
                return

            try:
                # Create parent directories in Nextcloud
                parent_folders = folder_path.split('/')
                current_path = ''
                for folder in parent_folders:
                    current_path = f"{current_path}/{folder}"
                    if not webdav_client.check(current_path):
                        webdav_client.mkdir(current_path)

                # Upload to Nextcloud
                webdav_client.upload(remote_path=full_remote_path, local_path=local_path)

                # Generate public share link
                share_response = nc.create_share(
                    path=f"/{full_remote_path}",
                    share_type=3,  # 3= public link
                    permissions=1   # 1= read-only
                )

                # Get the public URL and store it with the message
                public_url = share_response.data['url']

                text = ""
                try:
                    with open('data.json', 'r') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    data = {}

                reply_to_message = message.reply_to_message
                if reply_to_message:
                    text += ">>"+reply_to_message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+": "+str(reply_to_message.text) + "\n"

                text += ">"+message.date.strftime("%Y-%m-%d %H:%M")+": "+config.okos(message.from_user.id)+f": [File]({public_url})"
                data[str(message_id)] = text

                with open('data.json', 'w') as f:
                    json.dump(data, f)

            except Exception as e:
                logger.error(f"Nem tudtam feldolgozni ezt a képet: {str(e)}")
                raise

            finally:
                # Clean up temporary file
                if os.path.exists(local_path):
                    os.remove(local_path)

    except Exception as e:
        logger.error(f"Nem tudtam feldolgozni ezt a képet: {str(e)}")


async def list_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all currently kept messages."""
    if(update.effective_chat.id==config.chat_id):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            await update.message.reply_text("Nincs üzenet!")
            return
        if not data:
            await update.message.reply_text("Nincs üzenet!")
            return
        messages = "\n".join([f"{key}: {value}" for key, value in data.items()])
        await update.message.reply_text(f"Jelenlegi üzenetek:\n{messages}")


async def remove_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a specific message by its ID."""
    if(update.effective_chat.id==config.chat_id):
        if len(context.args) != 1:
            await update.message.reply_text("Használat: /remove <message_id>")
            return
        message_id = context.args[0]
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            await update.message.reply_text("Nincs üzenet!")
            return
        if message_id not in data:
            await update.message.reply_text(f"Nincs ilyen üzenet: {message_id}")
            return
        del data[message_id]
        with open('data.json', 'w') as f:
            json.dump(data, f)
        await update.message.reply_text(f"Üzenet törölve: {message_id}")


def send_email(messages):
    subject = 'Telegram üzenetek a csoportból'
    body = '\n'.join(messages)

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch the error."""
    print(f"{datetime.now()} - An error occurred: {context.error}")


def main() -> None:
    application = Application.builder().token(config.token).build()
    application.add_error_handler(error_handler)

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("apa", send_email_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("clear", clear_handler))
    application.add_handler(CommandHandler("list", list_messages_handler))
    application.add_handler(CommandHandler("del", remove_message_handler))

    # on non command i.e message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, echo_img2))
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, echo_img2))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
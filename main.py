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


async def pop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removing the last message from the dict."""
    if(update.effective_chat.id==config.chat_id):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except(FileNotFoundError, json.decoder.JSONDecodeError):
            # If the file does not exist, start with an empty dictionary
            data = {}
            return
        data.popitem()
        try:
            with open('data.json', 'w') as f:
                json.dump(data, f)
        except(FileNotFoundError, json.decoder.JSONDecodeError):
            # If the file does not exist, start with an empty dictionary
            data = {}
            return
        await update.message.reply_text("Az legutóbbi üzenet törölve!")


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
    application.add_handler(CommandHandler("pop", pop_handler))


    # on non command i.e message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, echo_img))
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, echo_img))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

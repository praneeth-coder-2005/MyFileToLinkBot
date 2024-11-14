from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os

# Environment variables for Heroku
TOKEN = os.getenv("BOT_TOKEN")
BIN_CHANNEL = int(os.getenv("BIN_CHANNEL"))

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me any file, and I'll give you a download link!")

def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.photo[-1]
    sent_message = context.bot.send_document(chat_id=BIN_CHANNEL, document=file.file_id)
    file_link = f"https://t.me/{context.bot.username}?start={sent_message.message_id}"
    update.message.reply_text(f"Here is your download link: {file_link}")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, send_file, abort
import os
import requests
import threading

# Telegram Bot Token and Channel ID
TOKEN = os.getenv("BOT_TOKEN")
BIN_CHANNEL = int(os.getenv("BIN_CHANNEL"))

# Initialize Flask App
app = Flask(__name__)

# Initialize Telegram Bot Updater
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Start Command for the Bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me any file, and I'll give you a direct download link!")

# Handle File Uploads
def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.photo[-1]
    sent_message = context.bot.send_document(chat_id=BIN_CHANNEL, document=file.file_id)
    file_link = f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com/file/{sent_message.message_id}"
    update.message.reply_text(f"Here is your download link: {file_link}")

# Flask Route to Serve Files
@app.route('/file/<int:message_id>')
def serve_file(message_id):
    try:
        bot_token = os.getenv("BOT_TOKEN")
        file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={message_id}"
        
        # Retrieve file path from Telegram API
        response = requests.get(file_url).json()
        file_path = response['result']['file_path']
        
        # Construct direct file download URL
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        return send_file(download_url, as_attachment=True)
    except:
        abort(404)  # If file not found or another error occurs

# Start the Bot in a Separate Thread
def start_bot():
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))
    updater.start_polling()

# Run both the Bot and Flask App
if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

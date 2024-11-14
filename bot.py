from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, send_file, abort, redirect
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
    # Create a download link in a shortened format
    file_link = f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com/dl/{sent_message.message_id}"
    update.message.reply_text(f"Here is your download link: {file_link}")

# Route to Serve Files with Shortened Link
@app.route('/dl/<int:message_id>')
def serve_file(message_id):
    try:
        bot_token = os.getenv("BOT_TOKEN")
        # Retrieve file ID from the channel message
        file_message = updater.bot.get_chat(BIN_CHANNEL).get_message(message_id)
        file_id = file_message.document.file_id if file_message.document else file_message.photo[-1].file_id

        # Fetch the file path from Telegram
        file_info = updater.bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}"

        # Redirect to the direct Telegram file URL
        return redirect(file_url)
    except:
        abort(404)  # Return 404 if the file is not found or an error occurs

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

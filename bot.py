from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, abort, redirect
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

# Root Endpoint to show that the app is running
@app.route('/')
def index():
    return "File-to-Link Bot is Running!"

# Start Command for the Bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me any file, and I'll give you a direct download link!")

# Handle File Uploads
def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.photo[-1]
    # Send the file to the BIN_CHANNEL
    sent_message = context.bot.send_document(chat_id=BIN_CHANNEL, document=file.file_id)
    # Hardcode the download link to use your specified Heroku app URL
    file_link = f"https://my-file-to-link-b4decad09203.herokuapp.com/dl/{sent_message.message_id}"
    update.message.reply_text(f"Here is your download link: {file_link}")
    print(f"Generated link: {file_link}")

# Route to Serve Files with Shortened Link
@app.route('/dl/<int:message_id>')
def serve_file(message_id):
    try:
        print(f"Attempting to serve file with message_id: {message_id}")
        # Retrieve the message from the channel using the message ID
        file_message = updater.bot.get_chat(BIN_CHANNEL).get_message(message_id)
        file_id = file_message.document.file_id if file_message.document else file_message.photo[-1].file_id

        # Fetch the file path from Telegram
        file_info = updater.bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

        # Redirect to the direct Telegram file URL
        return redirect(file_url)
    except Exception as e:
        print(f"Error serving file with message_id {message_id}: {e}")
        abort(404)  # If file is not found or an error occurs

# Start the Bot in a Separate Thread
def start_bot():
    print("Starting the Telegram bot...")
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))
    updater.start_polling()

# Run both the Bot and Flask App
if __name__ == "__main__":
    # Start the bot in a separate thread
    threading.Thread(target=start_bot).start()
    print("Starting Flask server...")
    # Run Flask directly without waitress
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, abort, redirect
import os
import threading

# Telegram Bot Token and Channel ID
TOKEN = os.getenv("BOT_TOKEN")
BIN_CHANNEL = int(os.getenv("BIN_CHANNEL"))

# Initialize Flask App
app = Flask(__name__)

# Initialize Telegram Bot Updater
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Variable to store the latest message ID for the file
latest_message_id = None

# Root Endpoint to serve the latest file
@app.route('/')
def index():
    global latest_message_id
    if latest_message_id is None:
        return "No file has been uploaded yet."
    else:
        try:
            # Retrieve the message from the channel using the latest message ID
            file_message = updater.bot.get_chat(BIN_CHANNEL).get_message(latest_message_id)
            file_id = file_message.document.file_id if file_message.document else file_message.photo[-1].file_id

            # Fetch the file path from Telegram
            file_info = updater.bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

            # Redirect to the direct Telegram file URL
            print(f"Redirecting to file URL: {file_url}")
            return redirect(file_url)
        except Exception as e:
            print(f"Error serving file with message_id {latest_message_id}: {e}")
            return "Error retrieving file. Please upload again.", 404

# Start Command for the Bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me any file, and I'll give you a direct download link!")

# Handle File Uploads and Update Latest Message ID
def handle_file(update: Update, context: CallbackContext) -> None:
    global latest_message_id
    file = update.message.document or update.message.photo[-1]
    # Send the file to the BIN_CHANNEL and store the message ID
    sent_message = context.bot.send_document(chat_id=BIN_CHANNEL, document=file.file_id)
    
    # Update the latest message ID to the newly uploaded file's message ID
    latest_message_id = sent_message.message_id
    print(f"Updated latest message ID to: {latest_message_id}")
    
    # Send the static link to the user
    file_link = "https://my-file-to-link-d1e1474ae14e.herokuapp.com/"
    update.message.reply_text(f"Here is your download link: {file_link}")
    print(f"Sent download link: {file_link}")

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

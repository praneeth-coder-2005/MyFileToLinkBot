from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, redirect
import os
import threading

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN")

# Initialize Flask App
app = Flask(__name__)

# Initialize Telegram Bot Updater
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Dictionary to store message_id -> file_url mapping
file_links = {}

# Root Endpoint to Show Bot Status
@app.route('/')
def index():
    return "File-to-Link Bot is Running!"

# Start Command for the Bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me any file, and I'll give you a direct download link! (Files can be up to 2GB)")

# Handle File Uploads and Generate Download Link
def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id
    
    # Generate a direct download link using Telegram's file URL
    file_info = context.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    
    # Store the generated link for this specific message ID
    message_id = update.message.message_id
    file_links[message_id] = file_url
    print(f"Stored file link for message_id {message_id}: {file_url}")

    # Send the dynamic download link to the user
    bot_url = f"https://my-file-to-link-d1e1474ae14e.herokuapp.com/download/{message_id}"
    update.message.reply_text(f"Here is your download link: {bot_url}")

# Route to Serve Files Using Message ID
@app.route('/download/<int:message_id>')
def serve_file(message_id):
    # Check if the message_id exists in our file links dictionary
    if message_id in file_links:
        file_url = file_links[message_id]
        print(f"Redirecting to file URL: {file_url}")
        return redirect(file_url)
    else:
        print(f"File with message_id {message_id} not found.")
        return "Error: File not found. Please re-upload.", 404

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

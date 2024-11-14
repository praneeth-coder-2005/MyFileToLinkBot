from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
import os
import random
import string

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_CHANNEL = int(os.getenv("DB_CHANNEL"))  # Private Channel ID for storing files
BASE_URL = "https://my-file-to-link-d1e1474ae14e.herokuapp.com/"  # Replace with your hosting URL

# Database connection
def get_db_connection():
    conn = sqlite3.connect('file_store.db')
    conn.row_factory = sqlite3.Row
    return conn

# Generate a unique download link
def generate_unique_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome to the File to Link Bot! Send me files up to 2GB, and I’ll give you a download link.")

# Handle file uploads
def handle_file_upload(update: Update, context: CallbackContext) -> None:
    file = update.message.document or update.message.video or update.message.photo[-1]
    file_id = file.file_id
    file_name = file.file_name if hasattr(file, 'file_name') else "file"
    user_id = update.message.from_user.id
    unique_link = generate_unique_link()

    # Forward the file to the private channel
    sent_message = context.bot.forward_message(chat_id=DB_CHANNEL, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
    message_id = sent_message.message_id

    # Store file metadata in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO files (user_id, file_id, message_id, file_name, unique_link) VALUES (?, ?, ?, ?, ?)', 
                   (user_id, file_id, message_id, file_name, unique_link))
    conn.commit()
    conn.close()

    # Send the download link to the user
    download_link = f"{BASE_URL}/download/{unique_link}"
    update.message.reply_text(f"File '{file_name}' uploaded successfully.\nHere is your download link: {download_link}")

# Serve files based on the unique link
def serve_file(update: Update, context: CallbackContext) -> None:
    unique_link = context.args[0] if context.args else None
    if not unique_link:
        update.message.reply_text("Please provide a valid file ID. Usage: /getfile <file_id>")
        return

    # Retrieve file metadata based on the unique link
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE unique_link = ?', (unique_link,))
    file = cursor.fetchone()
    conn.close()

    if not file:
        update.message.reply_text("File not found.")
        return

    # Send the file to the user using the message ID in the private channel
    context.bot.forward_message(chat_id=update.message.chat_id, from_chat_id=DB_CHANNEL, message_id=file['message_id'])
    update.message.reply_text(f"Here is your file: {file['file_name']}")

# Main function to set up the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video, handle_file_upload))
    dispatcher.add_handler(CommandHandler("getfile", serve_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

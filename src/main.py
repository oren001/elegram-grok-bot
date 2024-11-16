import logging
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config.config import TELEGRAM_TOKEN, BOT_USERNAME, DB_NAME, LOG_FORMAT, LOG_LEVEL
from src.database.message_store import MessageDatabase
from src.handlers.grok_handler import query_grok
from src.handlers.command_manager import CommandManager

# Configure logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database
db = MessageDatabase(DB_NAME)

# Will be initialized in main()
command_manager = None

async def handle_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /learn command to add new commands"""
    if not update.message or not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /learn command_name command_response\n"
            "Example: /learn hello Hello, I'm your friendly bot!"
        )
        return

    command_name = context.args[0]
    command_response = " ".join(context.args[1:])
    
    result = await command_manager.add_command(command_name, command_response)
    await update.message.reply_text(result)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text
    
    # Check if bot is mentioned
    is_bot_mention = BOT_USERNAME.lower() in message_text.lower()
    
    # Store message in database
    db.store_message(chat_id, user_id, username, message_text, is_bot_mention)
    
    # Only respond if bot is mentioned
    if is_bot_mention:
        # Get recent conversation context
        recent_messages = db.get_recent_context(chat_id)
        context_text = "\n".join([f"{username}: {text}" for username, text in recent_messages[::-1]])
        
        # Remove the bot username from the message for cleaner prompt
        prompt = message_text.replace(BOT_USERNAME, '').strip()
        
        # Get response from Grok
        response = await query_grok(context_text, prompt)
        
        # Send response
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    global command_manager
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Initialize command manager
    command_manager = CommandManager(application)
    
    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("learn", handle_learn))
    
    print("Bot started! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()

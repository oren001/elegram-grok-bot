import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config.config import TELEGRAM_TOKEN, BOT_USERNAME, DB_NAME, LOG_FORMAT, LOG_LEVEL
from src.database.message_store import MessageDatabase
from src.handlers.grok_handler import query_grok
from src.handlers.command_manager import CommandManager
from src.handlers.code_handler import CodeHandler

# Configure logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database
db = MessageDatabase(DB_NAME)

# Will be initialized in main()
command_manager = None
code_handler = None

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
        # Check if it's a programming request
        programming_keywords = ['create a command', 'add command', 'make a command']
        is_programming_request = any(keyword in message_text.lower() for keyword in programming_keywords)
        
        # Get recent conversation context
        recent_messages = db.get_recent_context(chat_id)
        context_text = "\n".join([f"{username}: {text}" for username, text in recent_messages[::-1]])
        
        # Remove the bot username from the message for cleaner prompt
        prompt = message_text.replace(BOT_USERNAME, '').strip()
        
        # Get response from Grok
        response = await query_grok(context_text, prompt)
        
        if is_programming_request:
            # Try to parse and implement the code
            parsed = code_handler.parse_grok_response(response)
            if parsed and 'command_name' in parsed and 'function_code' in parsed:
                result = await code_handler.implement_command(
                    parsed['command_name'],
                    parsed['function_code']
                )
                await update.message.reply_text(
                    f"{response}\n\nImplementation result: {result}",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        
        # Send normal response
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    global command_manager, code_handler
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Initialize handlers
    command_manager = CommandManager(application)
    code_handler = CodeHandler(application, db)
    
    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot started! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()

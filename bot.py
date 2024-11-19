import logging
import os
from datetime import datetime
import sqlite3
import aiohttp
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and API keys
TELEGRAM_TOKEN = '8128441937:AAH8fcknTZiqNWk1Iq5YfxHHev6kqdT2_Qk'
GROK_API_KEY = 'xai-LgvWmftz4Gwk9z9rQwoGVn4n3WNg4SubdoeSLBllbq9nxHilHT8p3WMfVdCKRBrqYsTyhf8KYJI5NMRs'
BOT_USERNAME = '@ourdudebot'

class MessageDatabase:
    def __init__(self, db_name='chat_memory.db'):
        self.conn = sqlite3.connect(db_name)
        self.setup_database()
    
    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                username TEXT,
                message_text TEXT,
                timestamp DATETIME,
                is_bot_mention BOOLEAN
            )
        ''')
        self.conn.commit()

    def store_message(self, chat_id, user_id, username, message_text, is_bot_mention):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO messages (chat_id, user_id, username, message_text, timestamp, is_bot_mention)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chat_id, user_id, username, message_text, datetime.now(), is_bot_mention))
        self.conn.commit()

    def get_recent_context(self, chat_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT username, message_text FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (chat_id, limit))
        return cursor.fetchall()

async def query_grok(context: str, prompt: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are an AI assistant in a Telegram group chat. You have access to the recent conversation context and can respond naturally when mentioned. You should:
1. Understand the context of the conversation
2. Respond appropriately to direct questions or requests
3. Be helpful and engaging while maintaining conversation flow
4. If asked to modify your own behavior or add new features, explain how you would implement them
5. Respond in a casual, friendly manner like a helpful friend in the chat"""

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Recent chat context:\n{context}\n\nCurrent message:\n{prompt}"}
        ],
        "model": "grok-beta",
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return "Sorry, I'm having trouble processing your request right now."
    except Exception as e:
        logger.error(f"Error querying Grok: {e}")
        return "I encountered an error while processing your request."

db = MessageDatabase()

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
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()

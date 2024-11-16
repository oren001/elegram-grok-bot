import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import aiohttp
import json
from typing import Dict, Any
from config.config import GROK_API_KEY

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
        print(f"Error querying Grok: {e}")
        return "I encountered an error while processing your request."

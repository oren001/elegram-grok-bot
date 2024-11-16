import sys
from pathlib import Path
import inspect
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import aiohttp
import json
from config.config import GROK_API_KEY

async def query_grok(context: str, prompt: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are an AI assistant that can modify its own code. When asked about adding new features:
1. Analyze the request
2. Generate the necessary Python code
3. Explain how to implement it
4. Return the code in a format that can be automatically added to the bot

If user asks you to add a new command, provide code that:
1. Uses the existing MessageDatabase class for data access
2. Returns implementation details in JSON format with:
   - command_name: name of the command
   - function_code: the Python code for the handler
   - description: what the command does
"""

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


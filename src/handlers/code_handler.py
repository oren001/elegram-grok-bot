import json
import ast
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

class CodeHandler:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        
    def validate_code(self, code_str: str) -> bool:
        try:
            ast.parse(code_str)
            return True
        except SyntaxError:
            return False
            
    async def implement_command(self, command_name: str, code_str: str) -> Optional[str]:
        if not self.validate_code(code_str):
            return "Invalid Python code"
            
        try:
            # Create the function dynamically
            namespace = {'db': self.db}
            exec(code_str, namespace)
            handler = namespace.get(f'handle_{command_name}')
            
            if handler:
                self.app.add_handler(CommandHandler(command_name, handler))
                return f"Successfully added /{command_name} command!"
            return "Could not find handler function in code"
        except Exception as e:
            return f"Error implementing command: {str(e)}"

    def parse_grok_response(self, response: str) -> Optional[Dict[str, Any]]:
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        return None

import json
from pathlib import Path
from typing import Dict, Any
from telegram.ext import CommandHandler, Application

class CommandManager:
    def __init__(self, app: Application):
        self.app = app
        self.commands_file = Path("config/custom_commands.json")
        self.commands: Dict[str, str] = self.load_commands()

    def load_commands(self) -> Dict[str, str]:
        if self.commands_file.exists():
            return json.loads(self.commands_file.read_text())
        return {}

    def save_commands(self):
        self.commands_file.parent.mkdir(exist_ok=True)
        self.commands_file.write_text(json.dumps(self.commands, indent=2))

    async def add_command(self, name: str, response: str):
        self.commands[name] = response
        self.save_commands()
        # Re-register the command handler
        self.app.add_handler(CommandHandler(name, self.handle_custom_command))
        return f"Command /{name} has been added successfully!"

    async def handle_custom_command(self, update: Any, context: Any):
        command = update.message.text.split()[0][1:]  # Remove the '/'
        if command in self.commands:
            await update.message.reply_text(self.commands[command])

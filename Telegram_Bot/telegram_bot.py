from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ApplicationBuilder,
    ContextTypes,
)
from os import environ
from dotenv import load_dotenv
from handlers import new_cuisine, add_item, edit_recipe, eco_cuisine, select_food, new_refrigerator

# Load environment variables from .env file
load_dotenv()

bot_token = environ.get("TELEGRAM_BOT_TOKEN")

if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")


new_app = ApplicationBuilder().token(bot_token).build()

# Define command handlers
new_app.add_handler(CommandHandler("newcuisine", new_cuisine))
new_app.add_handler(CommandHandler("newrefrigerator", new_refrigerator))
new_app.add_handler(CommandHandler("additem", add_item))
new_app.add_handler(CommandHandler("editrecipe", edit_recipe))
new_app.add_handler(CommandHandler("ecocuisine", eco_cuisine))
new_app.add_handler(CommandHandler("selectfood", select_food))

# Start the bot
new_app.run_polling()

# print("Bot is running...")
print("Bot is running... Press Ctrl+C to stop.")

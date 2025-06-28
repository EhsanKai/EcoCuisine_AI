from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ApplicationBuilder, ContextTypes


TOKEN = environ.get('TELEGRAM_BOT_TOKEN')  # Replace with your bot's token

# Define a command handler function
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("hello", hello))

# Start the bot
app.run_polling()

# print("Bot is running...")
print("Bot is running... Press Ctrl+C to stop.")


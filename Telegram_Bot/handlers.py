from telegram import Update
from telegram.ext import ContextTypes


# Define a command handler function
async def new_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}")


async def new_refrigerator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Create a new refrigerator, {update.effective_user.first_name}"
    )

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Add item to your refrigerator, {update.effective_user.first_name}"
    )


async def edit_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Edit your recipe, {update.effective_user.first_name}"
    )


async def eco_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Eco-friendly cuisine suggestions, {update.effective_user.first_name}"
    )


async def select_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Select food options, {update.effective_user.first_name}"
    )

from telegram import Update
from telegram.ext import ContextTypes
import sys
import os

# Add the DBs folder to the path so we can import our database classes
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "DBs"))
from refrigerator_db import RefrigeratorDB

# Initialize the refrigerator database handler
fridge_db = RefrigeratorDB()


# Define a command handler function
async def new_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}")


async def new_refrigerator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /newrefrigerator command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Check if user already has a refrigerator
    if fridge_db.user_has_refrigerator(user_id):
        # Load existing refrigerator and show items
        items = fridge_db.get_refrigerator_items(user_id)

        if not items:
            message = f"🧊 Welcome back to your refrigerator, {user_name}!\n\n"
            message += "Your refrigerator is currently empty.\n"
            message += "Use /additem to add items to your refrigerator!"
        else:
            message = f"🧊 Welcome back to your refrigerator, {user_name}!\n\n"
            message += "📋 Your current items:\n\n"

            for item in items:
                _, item_name, quantity, unit, expiry_date, _ = item
                message += f"• {item_name}: {quantity} {unit}"
                if expiry_date:
                    message += f" (expires: {expiry_date})"
                message += "\n"

            message += f"\n📊 Total items: {len(items)}"
            message += "\n\nUse /additem to add more items!"
    else:
        # Create new refrigerator
        success = fridge_db.create_user_refrigerator(user_id)

        if success:
            # Save user info
            fridge_db.save_user_info(
                user_id,
                update.effective_user.username,
                update.effective_user.first_name,
                update.effective_user.last_name,
            )

            message = f"🎉 Congratulations, {user_name}!\n\n"
            message += "🧊 Your new refrigerator has been created successfully!\n\n"
            message += "You can now:\n"
            message += "• Use /additem to add items to your refrigerator\n"
            message += "• Use /newrefrigerator to view your items\n"
            message += "• Use /ecocuisine to get eco-friendly recipe suggestions"
        else:
            message = f"❌ Sorry {user_name}, there was an error creating your refrigerator.\n"
            message += "Please try again later."

    await update.message.reply_text(message)


async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /additem command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Check if user has a refrigerator
    if not fridge_db.user_has_refrigerator(user_id):
        message = f"❌ {user_name}, you don't have a refrigerator yet!\n"
        message += "Use /newrefrigerator to create one first."
        await update.message.reply_text(message)
        return

    # Get the arguments (item details)
    args = context.args

    if not args:
        message = "📝 Please specify an item to add!\n\n"
        message += "Usage: /additem <item_name> [quantity] [unit]\n\n"
        message += "Examples:\n"
        message += "• /additem Apples 5 pieces\n"
        message += "• /additem Milk 1 liter\n"
        message += "• /additem Bread 2 loaves\n"
        message += "• /additem Eggs (default: 1 pieces)"
        await update.message.reply_text(message)
        return

    # Parse arguments
    item_name = args[0]
    quantity = 1
    unit = "pieces"

    if len(args) >= 2:
        try:
            quantity = int(args[1])
        except ValueError:
            unit = args[1]  # If second arg is not a number, treat it as unit

    if len(args) >= 3:
        unit = args[2]

    # Add item to refrigerator
    success = fridge_db.add_item_to_refrigerator(user_id, item_name, quantity, unit)

    if success:
        message = "✅ Successfully added to your refrigerator!\n\n"
        message += f"📦 Item: {item_name}\n"
        message += f"📊 Quantity: {quantity} {unit}\n\n"
        message += "Use /newrefrigerator to view all your items!"
    else:
        message = f"❌ Sorry {user_name}, there was an error adding the item.\n"
        message += "Please try again later."

    await update.message.reply_text(message)


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

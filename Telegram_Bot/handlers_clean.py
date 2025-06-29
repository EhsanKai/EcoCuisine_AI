from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
import sys
import os

# Add the DBs folder to the path so we can import our database classes
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "DBs"))
from refrigerator_db import RefrigeratorDB
from cuisine_db import CuisineDB

# Initialize the database handlers
fridge_db = RefrigeratorDB()
cuisine_db = CuisineDB()

# Store user states for conversation flow
user_states = {}


async def new_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /newcuisine command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Create user folder if it doesn't exist
    folder_created = cuisine_db.create_user_folder(user_id)

    # Check if user already has cuisine system
    if cuisine_db.user_has_cuisine_system(user_id):
        # Load existing cuisines and show them
        cuisines = cuisine_db.get_cuisines(user_id)

        if not cuisines:
            message = f"🍳 Welcome back to your cuisine collection, {user_name}!\n\n"
            message += "You don't have any cuisines yet.\n\n"
            message += "💡 Type the name of a cuisine to create it!\n"
            message += "Example: Type 'Lasagne' to create a lasagne.db file"
        else:
            message = f"🍳 Welcome back to your cuisine collection, {user_name}!\n\n"
            message += "📋 Your existing cuisines:\n\n"

            for cuisine in cuisines:
                cuisine_id, cuisine_name, cuisine_filename, description, _ = cuisine
                message += f"• {cuisine_name} ({cuisine_filename})"
                if description:
                    message += f" - {description}"
                message += "\n"

            message += f"\n📊 Total cuisines: {len(cuisines)}"
            message += "\n\n💡 Type the name of a new cuisine to create it!"

        # Set user state to expect cuisine name
        user_states[user_id] = "waiting_for_cuisine_name"
    else:
        # Create new cuisine system
        success = cuisine_db.create_cuisine_index_database(user_id)

        if success:
            if folder_created:
                message = f"🎉 Congratulations, {user_name}!\n\n"
                message += "📁 Your personal folder has been created!\n"
            else:
                message = f"🎉 Welcome back, {user_name}!\n\n"

            message += "🍳 Your cuisine system has been set up successfully!\n\n"
            message += "Now you can create your first cuisine:\n"
            message += "💡 Type the name of a cuisine to create it!\n"
            message += "Example: Type 'Lasagne' to create a lasagne.db file"

            # Set user state to expect cuisine name
            user_states[user_id] = "waiting_for_cuisine_name"
        else:
            message = f"❌ Sorry {user_name}, there was an error setting up your cuisine system.\n"
            message += "Please try again later."

    await update.message.reply_text(message)


async def new_refrigerator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /newrefrigerator command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Create user folder if it doesn't exist
    folder_created = fridge_db.create_user_folder(user_id)

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

            if folder_created:
                message = f"🎉 Congratulations, {user_name}!\n\n"
                message += "📁 Your personal folder has been created!\n"
            else:
                message = f"🎉 Welcome back, {user_name}!\n\n"

            message += "🧊 Your new refrigerator has been created successfully!\n\n"
            message += "You can now:\n"
            message += "• Use /additem to add items to your refrigerator\n"
            message += "• Use /newrefrigerator to view your items\n"
            message += "• Use /newcuisine to manage your cuisines"
        else:
            message = f"❌ Sorry {user_name}, there was an error creating your refrigerator.\n"
            message += "Please try again later."

    await update.message.reply_text(message)


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages for cuisine creation"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text.strip()

    # Check if user is in cuisine creation mode
    if user_id in user_states and user_states[user_id] == "waiting_for_cuisine_name":

        # Validate cuisine name
        if len(text) < 2 or len(text) > 50:
            message = "❌ Cuisine name must be between 2 and 50 characters.\n"
            message += "Please try again with a valid name."
            await update.message.reply_text(message)
            return

        # Check if cuisine already exists
        if cuisine_db.cuisine_exists(user_id, text):
            message = f"❌ A cuisine named '{text}' already exists!\n"
            message += "Please choose a different name or use /newcuisine to view existing cuisines."
            await update.message.reply_text(message)
            return

        # Create the cuisine
        cuisine_id = cuisine_db.create_specific_cuisine_database(user_id, text)

        if cuisine_id:
            # Clear user state
            user_states.pop(user_id, None)

            # Get the database filename
            safe_name = "".join(
                c for c in text if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_name = safe_name.replace(" ", "_").lower()
            db_filename = f"{safe_name}.db"

            message = f"🎉 Excellent, {user_name}!\n\n"
            message += f"🍳 Cuisine '{text}' has been created successfully!\n"
            message += f"📁 Database file: {db_filename}\n\n"
            message += "You can now add ingredients to this cuisine.\n"
            message += "Use /newcuisine to view all your cuisines."
        else:
            message = f"❌ Sorry {user_name}, there was an error creating the cuisine '{text}'.\n"
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


# Message handler for text input
text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)

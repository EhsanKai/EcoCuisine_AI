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
# Store user context (cuisine name, ingredients being added, etc.)
user_context = {}


def build_existing_cuisine_message(user_name, cuisines):
    if not cuisines:
        message = f"🍳 Welcome back to your cuisine collection, {user_name}!\n\n"
        message += "You don't have any cuisines yet.\n\n"
        message += "💡 Type the name of a cuisine to create it!\n"
        message += "Example: Type 'Lasagne' to create a lasagne.db file\n"
        message += "📝 Note: After creating, you'll be asked to add ingredients for 1 person."
    else:
        message = f"🍳 Welcome back to your cuisine collection, {user_name}!\n\n"
        message += "📋 Your existing cuisines:\n\n"
        for cuisine in cuisines:
            _, cuisine_name, _, description, _ = cuisine
            message += f"• {cuisine_name}"
            if description:
                message += f" - {description}"
            message += "\n"
        message += f"\n📊 Total cuisines: {len(cuisines)}"
        message += "\n\n💡 Type the name of a new cuisine to create it!"
        message += "\n📝 Note: After creating, you'll be asked to add ingredients for 1 person."
    return message

def build_new_cuisine_system_message(user_name, folder_created):
    if folder_created:
        message = f"🎉 Congratulations, {user_name}!\n\n"
        message += "📁 Your personal folder has been created!\n"
    else:
        message = f"🎉 Welcome back, {user_name}!\n\n"
    message += "🍳 Your cuisine system has been set up successfully!\n\n"
    message += "Now you can create your first cuisine:\n"
    message += "💡 Type the name of a cuisine to create it!\n"
    message += "Example: Type 'Lasagne' to create a lasagne.db file\n"
    message += "📝 Note: After creating, you'll be asked to add ingredients for 1 person."
    return message

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
        message = build_existing_cuisine_message(user_name, cuisines)
        # Set user state to expect cuisine name
        user_states[user_id] = "waiting_for_cuisine_name"
    else:
        # Create new cuisine system
        success = cuisine_db.create_cuisine_index_database(user_id)
        if success:
            message = build_new_cuisine_system_message(user_name, folder_created)
            # Set user state to expect cuisine name
            user_states[user_id] = "waiting_for_cuisine_name"
        else:
            message = f"❌ Sorry {user_name}, there was an error setting up your cuisine system.\n"
            message += "Please try again later."

    await update.message.reply_text(message)


def build_existing_refrigerator_message(user_name, items):
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
    return message

def build_new_refrigerator_message(user_name, folder_created):
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
    return message

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
        message = build_existing_refrigerator_message(user_name, items)
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
            message = build_new_refrigerator_message(user_name, folder_created)
        else:
            message = f"❌ Sorry {user_name}, there was an error creating your refrigerator.\n"
            message += "Please try again later."

    await update.message.reply_text(message)


async def add_ingredient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /addingredient command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Check if user has any cuisines
    if not cuisine_db.user_has_cuisine_system(user_id):
        message = f"❌ {user_name}, you don't have any cuisines yet!\n"
        message += "Use /newcuisine to create your first cuisine."
        await update.message.reply_text(message)
        return

    # Get user's cuisines
    cuisines = cuisine_db.get_cuisines(user_id)

    if not cuisines:
        message = f"❌ {user_name}, you don't have any cuisines yet!\n"
        message += "Use /newcuisine to create your first cuisine."
        await update.message.reply_text(message)
        return

    # Show available cuisines
    message = f"🍳 Select a cuisine to add ingredients, {user_name}!\n\n"
    message += "📋 Your cuisines:\n\n"

    for cuisine in cuisines:
        _, cuisine_name, _, description, _ = cuisine
        message += f"• {cuisine_name}"
        if description:
            message += f" - {description}"
        message += "\n"

    message += "\n💡 Type the name of the cuisine you want to add ingredients to!"
    message += "\n📝 Note: Ingredients will be for 1 person portions."

    # Set user state
    user_states[user_id] = "selecting_cuisine_for_ingredients"

    await update.message.reply_text(message)


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages for cuisine creation and ingredient addition"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text.strip()

    # Check user state
    current_state = user_states.get(user_id)

    if current_state == "waiting_for_cuisine_name":
        await handle_cuisine_creation(update, text, user_id, user_name)

    elif current_state == "selecting_cuisine_for_ingredients":
        await handle_cuisine_selection_for_ingredients(update, text, user_id, user_name)

    elif current_state == "adding_ingredients":
        await handle_ingredient_input(update, text, user_id, user_name)

    else:
        # No active conversation
        message = "👋 Hi! Use one of these commands:\n\n"
        message += "🍳 /newcuisine - Create or view cuisines\n"
        message += "🧊 /newrefrigerator - Create or view refrigerator\n"
        message += "📝 /addingredient - Add ingredients to cuisine\n"
        message += "🥗 /additem - Add items to refrigerator"
        await update.message.reply_text(message)


async def handle_cuisine_creation(update, text, user_id, user_name):
    """Handle the creation of a new cuisine"""

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
        # Get the database filename
        safe_name = "".join(
            c for c in text if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_name = safe_name.replace(" ", "_").lower()
        db_filename = f"{safe_name}.db"

        message = f"🎉 Excellent, {user_name}!\n\n"
        message += f"🍳 Cuisine '{text}' has been created successfully!\n"
        message += f"📁 Database file: {db_filename}\n\n"
        message += "Now let's add ingredients for 1 person!\n\n"
        message += "📝 Please enter ingredients in this format:\n"
        message += "ingredient_name amount unit [category] [notes]\n\n"
        message += "Examples:\n"
        message += "• Tomato 2 pieces vegetables\n"
        message += "• Olive Oil 2 tbsp condiments extra virgin\n"
        message += "• Ground Beef 200 grams meat lean\n"
        message += "• Salt 1 tsp spices\n\n"
        message += "Type 'done' when you finish adding ingredients."

        # Set user state and context
        user_states[user_id] = "adding_ingredients"
        user_context[user_id] = {"cuisine_name": text, "ingredients_added": 0}

        await update.message.reply_text(message)
    else:
        message = (
            f"❌ Sorry {user_name}, there was an error creating the cuisine '{text}'.\n"
        )
        message += "Please try again later."
        await update.message.reply_text(message)


async def handle_cuisine_selection_for_ingredients(update, text, user_id, user_name):
    """Handle cuisine selection for adding ingredients"""

    # Check if cuisine exists
    if not cuisine_db.cuisine_exists(user_id, text):
        message = f"❌ Cuisine '{text}' doesn't exist!\n"
        message += "Please type the exact name of an existing cuisine."
        await update.message.reply_text(message)
        return

    # Set up ingredient addition
    message = f"🍳 Great! Adding ingredients to '{text}' (for 1 person)\n\n"
    message += "📝 Please enter ingredients in this format:\n"
    message += "ingredient_name amount unit [category] [notes]\n\n"
    message += "Examples:\n"
    message += "• Tomato 2 pieces vegetables\n"
    message += "• Olive Oil 2 tbsp condiments extra virgin\n"
    message += "• Ground Beef 200 grams meat lean\n"
    message += "• Salt 1 tsp spices\n\n"
    message += "Type 'done' when you finish adding ingredients."

    # Set user state and context
    user_states[user_id] = "adding_ingredients"
    user_context[user_id] = {"cuisine_name": text, "ingredients_added": 0}

    await update.message.reply_text(message)


async def handle_ingredient_input(update, text, user_id, user_name):
    """Handle ingredient input during the adding process"""

    if text.lower() == "done":
        # Finish adding ingredients
        context_data = user_context.get(user_id, {})
        cuisine_name = context_data.get("cuisine_name", "Unknown")
        ingredients_count = context_data.get("ingredients_added", 0)

        message = f"✅ Finished adding ingredients to '{cuisine_name}'!\n\n"
        message += f"📊 Total ingredients added: {ingredients_count}\n\n"
        message += "You can:\n"
        message += "• Use /newcuisine to view your cuisines\n"
        message += "• Use /addingredient to add more ingredients\n"
        message += "• Use /ecocuisine to get recipe suggestions"

        # Clear user state and context
        user_states.pop(user_id, None)
        user_context.pop(user_id, None)

        await update.message.reply_text(message)
        return

    # Parse ingredient input
    parts = text.split()

    if len(parts) < 3:
        message = "❌ Please use the correct format:\n"
        message += "ingredient_name amount unit [category] [notes]\n\n"
        message += "Example: Tomato 2 pieces vegetables\n"
        message += "Type 'done' to finish."
        await update.message.reply_text(message)
        return

    ingredient_name = parts[0]
    amount = parts[1]
    unit = parts[2]
    category = parts[3] if len(parts) > 3 else "other"
    notes = " ".join(parts[4:]) if len(parts) > 4 else None

    # Get cuisine name from context
    context_data = user_context.get(user_id, {})
    cuisine_name = context_data.get("cuisine_name")

    if not cuisine_name:
        message = (
            f"❌ Error: Lost cuisine context. Please start over with /addingredient"
        )
        user_states.pop(user_id, None)
        user_context.pop(user_id, None)
        await update.message.reply_text(message)
        return

    # Add ingredient to cuisine
    success = cuisine_db.add_ingredient_to_cuisine(
        user_id, cuisine_name, ingredient_name, amount, unit, notes, category
    )

    if success:
        # Update context
        user_context[user_id]["ingredients_added"] += 1
        ingredients_count = user_context[user_id]["ingredients_added"]

        message = f"✅ Added ingredient #{ingredients_count}:\n"
        message += f"• {ingredient_name}: {amount} {unit}"
        if category != "other":
            message += f" ({category})"
        if notes:
            message += f" - {notes}"
        message += "\n\n"
        message += "Add another ingredient or type 'done' to finish."

        await update.message.reply_text(message)
    else:
        message = f"❌ Error adding ingredient '{ingredient_name}'. Please try again."
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

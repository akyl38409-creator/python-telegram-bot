import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8245116257

USERS_FILE = "users.json"
MENU_FILE = "menu.json"
ORDERS_FILE = "orders.json"

def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data(USERS_FILE)
menu = {"Бургер": {"price": 200}, "Пицца": {"price": 500}}
orders = load_data(ORDERS_FILE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {"name": update.effective_user.first_name, "cart": [], "role": "user"}
        save_data(USERS_FILE, users)
        await update.message.reply_text("👋 Добро пожаловать!")
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Меню", callback_data="menu")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выбери:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Выбери:", reply_markup=reply_markup)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = "📋 Меню:\n"
    keyboard = []

    for name, info in menu.items():
        text += f"{name} — {info['price']} сом\n"
        keyboard.append([InlineKeyboardButton(f"➕ {name}", callback_data=f"add_{name}")])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item = query.data.replace("add_", "")
    user_id = str(update.effective_user.id)

    users[user_id]["cart"].append(item)
    save_data(USERS_FILE, users)

    await query.edit_message_text(f"✅ {item} добавлен!")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    cart = users[user_id]["cart"]

    if not cart:
        await query.edit_message_text("Корзина пуста")
        return

    text = "\n".join(cart)
    await query.edit_message_text(f"🛒 {text}")

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "main":
        await show_main_menu(update, context)
    elif data == "menu":
        await show_menu(update, context)
    elif data.startswith("add_"):
        await add_to_cart(update, context)
    elif data == "cart":
        await show_cart(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()

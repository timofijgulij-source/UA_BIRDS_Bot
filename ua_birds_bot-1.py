import telebot
import random
import time
import json
import os
from datetime import datetime, timedelta

# === ТОКЕН БОТА ===
TOKEN = "8688420629:AAHR8ls_zadYVAugf82f5GqR_tCD9GQ2aNM"
ADMIN_ID = 5822921179  # ← встав сюди свій Telegram ID (можна дізнатись у @userinfobot)
bot = telebot.TeleBot(TOKEN)

# === ФАЙЛ ЗБЕРЕЖЕННЯ ===
SAVE_FILE = "data.json"

# === СПИСОК ПТАХІВ ===
birds = {
    "Common": [
        "Горобець польовий", "Синиця велика", "Голуб сизий", "Грак", "Галка",
        "Ворона сіра", "Сорока звичайна", "Горлиця садова", "Шпак", "Ластівка сільська",
        "Плиска біла", "Зяблик", "Жайворонок польовий", "Дрізд чорний", "Зеленяк",
        "Щиглик", "Синиця блакитна", "Вівсянка звичайна", "Крук", "Горобець хатній"
    ],
    "Uncommon": [
        "Вільшанка", "Великий строкатий дятел", "Сойка", "Одуд", "Плиска жовта",
        "Мухоловка сіра", "Соловейко східний", "Повзик звичайний", "Підкоришник звичайний", "Кропив'янка чорноголова",
        "Костогриз", "Жайворонок чубатий", "Крутиголовка", "Чиж", "Щедрик європейський"
    ],
    "Rare": [
        "Золотомушка жовточуба", "Просянка", "Яструб малий", "Яструб великий",
        "Куріпка сіра", "Чайка чубата", "Дрізд білобровий",
        "Синиця довгохвоста", "Плиска гірська", "Сова вухата", "Вівчарик жовтобровий"
    ],
    "Epic": [
        "Жовна зелена", "Тинівка лісова", "Золотомушка червоночуба",
        "Голуб-синяк", "Сорокопуд сірий"
    ],
    "Legendary": [
        "Дятел трипалий", "Дрохва"
    ]
}

rarity_emoji = {
    "Common": "⚪",
    "Uncommon": "🟢",
    "Rare": "🔵",
    "Epic": "🟣",
    "Legendary": "🟡"
}

# === ІВЕНТ: ГЛУШЕЦЬ (ЕКСКЛЮЗИВНИЙ) ===
EVENT_TOKENS_NEEDED = 20
EVENT_TOKEN_CHANCE = 15
SHOP_MAX_TOTAL = 18
SHOP_MAX_WEEKLY = 9
COOLDOWN = 7200

EVENT_START = datetime(2026, 4, 17, 12, 0)
EVENT_END = datetime(2026, 5, 1, 12, 0)

# === ІВЕНТ: ПАСХАЛЬНІ ПТАХИ (ЕКСКЛЮЗИВНИЙ) ===
EASTER_START = datetime(2026, 4, 10, 13, 0)
EASTER_END = datetime(2026, 4, 17, 11, 0)
CARDS_PATH = "/storage/emulated/0/UA_BIRDS/"

def get_card_path(bird_name):
    # Замінюємо пробіл на _ і шукаємо файл
    filename = bird_name.replace(" ", "_") + ".jpg"
    path = CARDS_PATH + filename
    if os.path.exists(path):
        return path
    return None

EASTER_BIRDS = [
    ("Священний мартин", "Common"),
    ("Глазурна плиска", "Uncommon"),
    ("Писанкова синиця велика", "Rare"),
    ("Глазурна Золотомушка жовточуба", "Epic"),
    ("Священна жовна сива", "Legendary"),
]

EASTER_CHANCES = {
    "Common": 60,
    "Uncommon": 25,
    "Rare": 10,
    "Epic": 4.5,
    "Legendary": 0.5
}

def get_easter_bird():
    roll = random.uniform(0, 100)
    if roll <= 0.5:
        rarity = "Legendary"
    elif roll <= 5:
        rarity = "Epic"
    elif roll <= 15:
        rarity = "Rare"
    elif roll <= 40:
        rarity = "Uncommon"
    else:
        rarity = "Common"
    bird = next(b for b, r in EASTER_BIRDS if r == rarity)
    return bird, rarity

# === ПРОМОКОД ===
PROMO_CODE = "Exclusive bird"
PROMO_BIRD = "Вівчарик жовтобровий"
PROMO_RARITY = "Rare"
PROMO_START = datetime(2026, 4, 10, 13, 0)
PROMO_END = datetime(2026, 4, 13, 13, 0)


def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "inventory": {},
            "last_search": 0,
            "last_easter_search": 0,
            "event_tokens": 0,
            "event_claimed": False,
            "shop_total": 0,
            "shop_weekly": 0,
            "shop_week_reset": "",
            "total_searches": 0,
            "promo_used": False,
            "joined": datetime.now().strftime("%d.%m.%Y"),
            "chat_id": 0
        }
    # Додаємо нові поля старим юзерам якщо їх нема
    user = data[uid]
    if "total_searches" not in user: user["total_searches"] = 0
    if "joined" not in user: user["joined"] = "невідомо"
    if "chat_id" not in user: user["chat_id"] = 0
    if "promo_used" not in user: user["promo_used"] = False
    return user

def get_all_chat_ids(data):
    return [u["chat_id"] for u in data.values() if u.get("chat_id", 0) != 0]

def get_random_bird():
    roll = random.uniform(0, 100)
    if roll <= 0.5:
        rarity = "Legendary"
    elif roll <= 5:
        rarity = "Epic"
    elif roll <= 15:
        rarity = "Rare"
    elif roll <= 40:
        rarity = "Uncommon"
    else:
        rarity = "Common"
    return random.choice(birds[rarity]), rarity

def get_bird_rarity(bird_name):
    for rarity, bird_list in birds.items():
        if bird_name in bird_list:
            return rarity
    return None

def check_weekly_reset(user):
    today = datetime.now().strftime("%Y-%W")
    if user["shop_week_reset"] != today:
        user["shop_weekly"] = 0
        user["shop_week_reset"] = today

def main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🔍 Пошук птаха", "🎒 Інвентар")
    keyboard.row("🎪 Івент (Глушець)", "🐣 Івент (Пасха)")
    keyboard.row("🦅 Підтримка автора")
    return keyboard

# === /start ===
@bot.message_handler(commands=["start"])
def start(message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    user["chat_id"] = message.chat.id  # зберігаємо для розсилки
    name = message.from_user.first_name
    is_new = user["last_search"] == 0 and not user["inventory"]

    if is_new:
        msg = f"👑 Вітаємо вас у *Королівстві птахів*, {name}!\n\nЛаскаво просимо вас у це місце 🐦\n\nЯк подарунок вам нараховується *5 подарункових пошуків птахів*!\n\n"
        found = []
        for _ in range(5):
            bird, rarity = get_random_bird()
            user["inventory"][bird] = user["inventory"].get(bird, 0) + 1
            found.append(f"{rarity_emoji[rarity]} {bird} [{rarity}]")
        msg += "Твої перші птахи:\n" + "\n".join(found)
        msg += "\n\n🔍 /search — шукати птаха\n🎒 /inventory — інвентар\n🎪 /event — івент Глушець\n🐣 /easter — Пасхальний івент\n🏪 /shop — магазин обміну"
        save_data(data)
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id,
            f"🐦 З поверненням, {name}!\n\n🔍 /search\n🎒 /inventory\n🎪 /event\n🐣 /easter\n🏪 /shop",
            reply_markup=main_keyboard())

# === /search ===
@bot.message_handler(commands=["search"])
def search(message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    now = time.time()

    elapsed = now - user["last_search"]
    if elapsed < COOLDOWN:
        remaining = COOLDOWN - elapsed
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        bot.send_message(message.chat.id,
            f"⏳ Наступний пошук через *{h}г {m}хв*.", parse_mode="Markdown")
        return

    user["last_search"] = now
    user["total_searches"] = user.get("total_searches", 0) + 1
    user["chat_id"] = message.chat.id
    bird, rarity = get_random_bird()
    user["inventory"][bird] = user["inventory"].get(bird, 0) + 1
    count = user["inventory"][bird]
    emoji = rarity_emoji[rarity]

    msg = f"🔍 Ти знайшов птаха!\n\n{emoji} *{bird}* [{rarity}]\nУ тебе: {count} шт.\n"

    if rarity == "Legendary":
        msg += "\n🌟 *Вам справді дуже повезло!*\n"

    # Шанс токена глушця
    if not user["event_claimed"] and EVENT_START <= datetime.now() < EVENT_END:
        if random.uniform(0, 100) <= EVENT_TOKEN_CHANCE:
            user["event_tokens"] = min(user["event_tokens"] + 1, EVENT_TOKENS_NEEDED)
            tokens = user["event_tokens"]
            msg += f"\n🪙 *Токен Глушця випав!*\nЗібрано: {tokens}/{EVENT_TOKENS_NEEDED}"
            if tokens >= EVENT_TOKENS_NEEDED:
                msg += f"\n\n🏆 Напиши /claim щоб забрати *Глушець (Collectible)*!"

    msg += "\n\n⏰ Наступний пошук через *2 години*."
    save_data(data)

    card_path = get_card_path(bird)
    if card_path:
        with open(card_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=msg, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# === /promo ===
@bot.message_handler(commands=["promo"])
def promo(message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    now_dt = datetime.now()

    # Витягуємо текст після /promo
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
            "🎟 Введи промокод так:\n`/promo КОД`", parse_mode="Markdown")
        return

    code = parts[1].strip()

    if code.lower() == PROMO_CODE.lower():
        if now_dt < PROMO_START:
            bot.send_message(message.chat.id,
                f"⏳ Цей промокод ще не активний!\nСтарт: {PROMO_START.strftime('%d.%m о %H:%M')}")
            return
        if now_dt > PROMO_END:
            bot.send_message(message.chat.id,
                "❌ Термін дії цього промокоду минув!")
            return
        if user.get("promo_used"):
            bot.send_message(message.chat.id,
                "❌ Ти вже використав цей промокод!")
            return

        user["promo_used"] = True
        user["inventory"][PROMO_BIRD] = user["inventory"].get(PROMO_BIRD, 0) + 1
        save_data(data)
        bot.send_message(message.chat.id,
            f"🎟 Промокод активовано!\n\n"
            f"{rarity_emoji[PROMO_RARITY]} *{PROMO_BIRD}* [{PROMO_RARITY}]\n\n"
            f"⏰ Промокод діє до {PROMO_END.strftime('%d.%m о %H:%M')}",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "❌ Невірний промокод!")

# === /easter ===
@bot.message_handler(commands=["easter"])
def easter(message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    now_dt = datetime.now()
    now_ts = time.time()

    if now_dt < EASTER_START:
        days = (EASTER_START - now_dt).days
        bot.send_message(message.chat.id,
            f"🐣 *Пасхальний івент*\n\n⏳ Ще не почався! Старт через {days} днів\n({EASTER_START.strftime('%d.%m о %H:%M')})",
            parse_mode="Markdown")
        return

    if now_dt >= EASTER_END:
        bot.send_message(message.chat.id,
            "🐣 *Пасхальний івент завершився!*\n\nЦі птахи більше недоступні 🔒",
            parse_mode="Markdown")
        return

    # Перевірка кулдауну
    last = user.get("last_easter_search", 0)
    elapsed = now_ts - last
    if elapsed < EASTER_COOLDOWN:
        remaining = EASTER_COOLDOWN - elapsed
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        bot.send_message(message.chat.id,
            f"🐣 Наступний пасхальний пошук через *{h}г {m}хв*.",
            parse_mode="Markdown")
        return

    user["last_easter_search"] = now_ts
    bird, rarity = get_easter_bird()
    user["inventory"][bird] = user["inventory"].get(bird, 0) + 1
    count = user["inventory"][bird]
    emoji = rarity_emoji[rarity]
    hours_left = int((EASTER_END - now_dt).total_seconds() // 3600)

    save_data(data)
    bot.send_message(message.chat.id,
        f"🐣 *Пасхальний пошук!*\n\n{emoji} *{bird}* [{rarity}]\nУ тебе: {count} шт.\n\n"
        f"⏰ Наступний пошук через *12 годин*.\n"
        f"🕐 До кінця івенту: ~{hours_left} год.",
        parse_mode="Markdown"
    )

# === /event ===
@bot.message_handler(commands=["event"])
def event(message):
    data = load_data()
    user = get_user(data, str(message.from_user.id))
    tokens = user["event_tokens"]
    days_left = max(0, (EVENT_END - datetime.now()).days)
    now = datetime.now()

    if now < EVENT_START:
        days_to_start = (EVENT_START - now).days
        status = f"⏳ Івент ще не почався! Старт через {days_to_start} днів\n({EVENT_START.strftime('%d.%m о %H:%M')})"
    elif user["event_claimed"]:
        status = "✅ Ти вже отримав картку Глушець!"
    elif tokens >= EVENT_TOKENS_NEEDED:
        status = "🏆 Готово! Напиши /claim щоб забрати нагороду!"
    else:
        status = f"🪙 Зібрано токенів: *{tokens}/{EVENT_TOKENS_NEEDED}*"

    bot.send_message(message.chat.id,
        f"🎪 *Івент: Глушець*\n\n"
        f"{status}\n\n"
        f"📅 Залишилось: {days_left} днів\n"
        f"🎯 Шанс токена при пошуку: 15%\n\n"
        f"💱 Магазин (/shop):\n"
        f"• 7 Uncommon → 1 жетон\n"
        f"• 5 Rare → 3 жетони\n"
        f"• 3 Epic → 5 жетонів\n"
        f"• Ліміт: 9/тиждень, 18 за весь івент",
        parse_mode="Markdown"
    )

# === СЕСІЇ ВИБОРУ КАРТОК ===
# {user_id: {"rarity": "Uncommon", "needed": 7, "reward": 1, "selected": {"Горобець": 2}}}
shop_sessions = {}

# === /shop ===
@bot.message_handler(commands=["shop"])
def shop(message):
    show_shop_menu(message.chat.id, message.from_user.id)

def show_shop_menu(chat_id, user_id):
    data = load_data()
    user = get_user(data, str(user_id))
    check_weekly_reset(user)
    save_data(data)

    weekly_left = SHOP_MAX_WEEKLY - user["shop_weekly"]
    total_left = SHOP_MAX_TOTAL - user["shop_total"]
    real_left = min(weekly_left, total_left)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🟢 7 Uncommon → 1 жетон", callback_data="shop_uncommon"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔵 5 Rare → 3 жетони", callback_data="shop_rare"))
    keyboard.add(telebot.types.InlineKeyboardButton("🟣 3 Epic → 5 жетонів", callback_data="shop_epic"))

    bot.send_message(chat_id,
        f"🏪 *Магазин обміну*\n\n"
        f"🪙 Твої токени: *{user['event_tokens']}/{EVENT_TOKENS_NEEDED}*\n"
        f"📦 Можна купити ще: *{real_left}* жетонів\n"
        f"(тижд: {weekly_left}/9 | всього: {total_left}/18)\n\n"
        f"Обери що хочеш обміняти:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def show_bird_selection(call, rarity, needed, reward):
    user_id = call.from_user.id
    data = load_data()
    user = get_user(data, str(user_id))
    inv = user["inventory"]

    # Птахи потрібної рідкості в інвентарі
    available = {b: c for b, c in inv.items() if get_bird_rarity(b) == rarity and c > 0}

    if not available:
        bot.answer_callback_query(call.id, f"❌ У тебе немає карток {rarity}!")
        return

    total = sum(available.values())
    if total < needed:
        bot.answer_callback_query(call.id, f"❌ Потрібно {needed} карток, у тебе лише {total}!")
        return

    # Створюємо сесію
    shop_sessions[user_id] = {
        "rarity": rarity,
        "needed": needed,
        "reward": reward,
        "selected": {}
    }

    send_selection_message(call.message.chat.id, user_id, available)

def send_selection_message(chat_id, user_id, available=None):
    data = load_data()
    user = get_user(data, str(user_id))
    session = shop_sessions.get(user_id)
    if not session:
        return

    if available is None:
        inv = user["inventory"]
        available = {b: c for b, c in inv.items() if get_bird_rarity(b) == session["rarity"] and c > 0}

    selected = session["selected"]
    total_selected = sum(selected.values())
    needed = session["needed"]
    rarity = session["rarity"]
    reward = session["reward"]

    text = (f"🔄 *Вибір карток для обміну*\n"
            f"Рідкість: {rarity} | Потрібно: {needed}\n"
            f"Вибрано: *{total_selected}/{needed}*\n\n")

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)

    for bird, count in available.items():
        sel_count = selected.get(bird, 0)
        max_can_select = min(count, needed - total_selected + sel_count)
        if sel_count > 0:
            btn_text = f"✅ {bird} (є: {count}, вибрано: {sel_count})"
        else:
            btn_text = f"{bird} (є: {count})"
        keyboard.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=f"sel_{bird}"))

    # Кнопки підтвердження
    if total_selected == needed:
        keyboard.add(telebot.types.InlineKeyboardButton(f"🔄 Обміняти на +{reward} 🪙", callback_data="confirm_burn"))
    keyboard.add(telebot.types.InlineKeyboardButton("❌ Скасувати", callback_data="cancel_shop"))

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def handle_shop_choice(call):
    if call.data == "shop_uncommon":
        show_bird_selection(call, "Uncommon", 7, 1)
    elif call.data == "shop_rare":
        show_bird_selection(call, "Rare", 5, 3)
    elif call.data == "shop_epic":
        show_bird_selection(call, "Epic", 3, 5)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def handle_bird_select(call):
    user_id = call.from_user.id
    session = shop_sessions.get(user_id)
    if not session:
        bot.answer_callback_query(call.id, "❌ Сесія закінчилась, почни знову /shop")
        return

    bird = call.data[4:]
    selected = session["selected"]
    needed = session["needed"]
    total_selected = sum(selected.values())

    data = load_data()
    user = get_user(data, str(user_id))
    in_inv = user["inventory"].get(bird, 0)
    already_sel = selected.get(bird, 0)

    if already_sel >= in_inv:
        # Знімаємо вибір
        del selected[bird]
        bot.answer_callback_query(call.id, f"↩️ {bird} знято з вибору")
    elif total_selected >= needed:
        bot.answer_callback_query(call.id, f"⚠️ Вже вибрано {needed}/{needed}!")
        return
    else:
        selected[bird] = already_sel + 1
        bot.answer_callback_query(call.id, f"✅ {bird} додано!")

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_selection_message(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_burn")
def handle_confirm_burn(call):
    user_id = call.from_user.id
    session = shop_sessions.get(user_id)
    if not session:
        bot.answer_callback_query(call.id, "❌ Сесія закінчилась!")
        return

    data = load_data()
    user = get_user(data, str(user_id))
    check_weekly_reset(user)

    weekly_left = SHOP_MAX_WEEKLY - user["shop_weekly"]
    total_left = SHOP_MAX_TOTAL - user["shop_total"]
    real_left = min(weekly_left, total_left)

    if real_left <= 0:
        bot.answer_callback_query(call.id, "❌ Ліміт магазину вичерпано!")
        del shop_sessions[user_id]
        return

    selected = session["selected"]
    reward = session["reward"]
    inv = user["inventory"]
    removed = []

    for bird, count in selected.items():
        inv[bird] = inv.get(bird, 0) - count
        if inv[bird] <= 0:
            del inv[bird]
        removed.append(f"{bird} x{count}")

    actual = min(reward, real_left, EVENT_TOKENS_NEEDED - user["event_tokens"])
    user["event_tokens"] += actual
    user["shop_weekly"] += actual
    user["shop_total"] += actual

    del shop_sessions[user_id]
    save_data(data)

    msg = (f"✅ *Обмін успішний!*\n\n"
           f"🔄 Обміняно: {', '.join(removed)}\n"
           f"+{actual} 🪙 | Всього: *{user['event_tokens']}/{EVENT_TOKENS_NEEDED}*")

    if user["event_tokens"] >= EVENT_TOKENS_NEEDED:
        msg += "\n\n🏆 Напиши /claim щоб забрати *Глушець (Collectible)*!"

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_shop")
def handle_cancel_shop(call):
    user_id = call.from_user.id
    if user_id in shop_sessions:
        del shop_sessions[user_id]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id, "❌ Скасовано")
    bot.send_message(call.message.chat.id, "Магазин закрито. /shop щоб відкрити знову.")

@bot.message_handler(commands=["buy1"])
def buy1(message): show_shop_menu(message.chat.id, message.from_user.id)

@bot.message_handler(commands=["buy2"])
def buy2(message): show_shop_menu(message.chat.id, message.from_user.id)

@bot.message_handler(commands=["buy3"])
def buy3(message): show_shop_menu(message.chat.id, message.from_user.id)


# === /claim ===
@bot.message_handler(commands=["claim"])
def claim(message):
    data = load_data()
    user = get_user(data, str(message.from_user.id))

    if user["event_claimed"]:
        bot.send_message(message.chat.id, "✅ Ти вже забрав картку Глушець!")
        return
    if user["event_tokens"] < EVENT_TOKENS_NEEDED:
        bot.send_message(message.chat.id,
            f"❌ Ще не вистачає! {user['event_tokens']}/{EVENT_TOKENS_NEEDED} токенів")
        return

    user["event_claimed"] = True
    user["inventory"]["Глушець (Collectible)"] = 1
    save_data(data)
    bot.send_message(message.chat.id,
        "🏆 Вітаю! Ти отримав *Глушець (Collectible)*!\n\nВін у твоєму інвентарі 🎉",
        parse_mode="Markdown"
    )

# === ІНВЕНТАР З КАРТКАМИ ===
inv_sessions = {}  # {user_id: {"cards": [...], "index": 0}}

def get_all_user_cards(inv):
    cards = []
    # Спочатку Collectible
    for b, c in inv.items():
        if "Collectible" in b:
            cards.append((b, c, "Collectible"))
    # Потім по рідкості
    for rarity in ["Legendary", "Epic", "Rare", "Uncommon", "Common"]:
        for b, c in inv.items():
            if b in birds.get(rarity, []):
                cards.append((b, c, rarity))
    return cards

def send_inventory_card(chat_id, user_id, index=0, message_id=None):
    data = load_data()
    user = get_user(data, str(user_id))
    inv = user["inventory"]

    if not inv:
        bot.send_message(chat_id, "🎒 Інвентар порожній. Спробуй /search!")
        return

    cards = get_all_user_cards(inv)
    if not cards:
        bot.send_message(chat_id, "🎒 Інвентар порожній!")
        return

    index = max(0, min(index, len(cards) - 1))
    inv_sessions[user_id] = {"cards": cards, "index": index}

    bird, count, rarity = cards[index]
    emoji = rarity_emoji.get(rarity, "✨")
    total = len(cards)

    caption = (f"🎒 *Інвентар* [{index+1}/{total}]\n\n"
               f"{emoji} *{bird}*\n"
               f"Рідкість: {rarity}\n"
               f"Кількість: {count} шт.")

    keyboard = telebot.types.InlineKeyboardMarkup()
    btns = []
    if index > 0:
        btns.append(telebot.types.InlineKeyboardButton("◀️", callback_data=f"inv_{index-1}"))
    btns.append(telebot.types.InlineKeyboardButton(f"{index+1}/{total}", callback_data="inv_none"))
    if index < total - 1:
        btns.append(telebot.types.InlineKeyboardButton("▶️", callback_data=f"inv_{index+1}"))
    keyboard.row(*btns)
    keyboard.add(telebot.types.InlineKeyboardButton("❌ Закрити", callback_data="inv_close"))

    card_path = get_card_path(bird)

    try:
        if message_id:
            bot.delete_message(chat_id, message_id)
    except:
        pass

    if card_path:
        with open(card_path, "rb") as photo:
            bot.send_photo(chat_id, photo, caption=caption, parse_mode="Markdown", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=keyboard)

@bot.message_handler(commands=["inventory"])
def inventory(message):
    send_inventory_card(message.chat.id, message.from_user.id, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("inv_"))
def handle_inventory_nav(call):
    user_id = call.from_user.id
    data_part = call.data[4:]

    if data_part == "none":
        bot.answer_callback_query(call.id)
        return
    if data_part == "close":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.answer_callback_query(call.id)
        return

    index = int(data_part)
    bot.answer_callback_query(call.id)
    send_inventory_card(call.message.chat.id, user_id, index, call.message.message_id)

# === /help ===
@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id,
        "📖 *UA Birds — список команд*\n\n"
        "🔍 /search — шукати птаха (раз на 2 год)\n"
        "🎒 /inventory — твій інвентар\n"
        "👤 /profile — твій профіль\n\n"
        "🐣 /easter — Пасхальний івент (раз на 12 год)\n"
        "🎪 /event — івент Глушець\n"
        "🏪 /shop — магазин обміну жетонів\n"
        "🎟 /promo КОД — активувати промокод\n\n"
        "🏆 /claim — забрати нагороду івенту\n\n"
        "Рідкості птахів:\n"
        "⚪ Common (60%) | 🟢 Uncommon (25%)\n"
        "🔵 Rare (10%) | 🟣 Epic (4.5%) | 🟡 Legendary (0.5%)",
        parse_mode="Markdown"
    )

# === /profile ===
@bot.message_handler(commands=["profile"])
def profile(message):
    data = load_data()
    user = get_user(data, message.from_user.id)
    inv = user["inventory"]
    name = message.from_user.first_name

    total_cards = sum(inv.values())
    unique_cards = len(inv)
    searches = user.get("total_searches", 0)
    joined = user.get("joined", "невідомо")

    # Рахуємо по рідкостях
    counts = {}
    for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
        counts[rarity] = sum(c for b, c in inv.items() if b in birds.get(rarity, []))
    collectibles = sum(c for b, c in inv.items() if "Collectible" in b)

    bot.send_message(message.chat.id,
        f"👤 *Профіль: {name}*\n\n"
        f"📅 В грі з: {joined}\n"
        f"🔍 Пошуків: {searches}\n"
        f"🃏 Карток всього: {total_cards} ({unique_cards} унікальних)\n\n"
        f"⚪ Common: {counts['Common']}\n"
        f"🟢 Uncommon: {counts['Uncommon']}\n"
        f"🔵 Rare: {counts['Rare']}\n"
        f"🟣 Epic: {counts['Epic']}\n"
        f"🟡 Legendary: {counts['Legendary']}\n"
        f"✨ Collectible: {collectibles}\n\n"
        f"🪙 Токени Глушця: {user['event_tokens']}/{EVENT_TOKENS_NEEDED}",
        parse_mode="Markdown"
    )

# === /announce (тільки для адміна) ===
@bot.message_handler(commands=["announce"])
def announce(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Ця команда тільки для адміна!")
        return

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Використання: /announce ТЕКСТ")
        return

    text = parts[1]
    data = load_data()
    chat_ids = get_all_chat_ids(data)
    sent = 0

    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id, f"📢 *Оголошення від UA Birds:*\n\n{text}", parse_mode="Markdown")
            sent += 1
            time.sleep(0.05)  # щоб не перевантажити Telegram
        except Exception:
            pass

    bot.send_message(message.chat.id, f"✅ Надіслано {sent}/{len(chat_ids)} користувачам.")

# === КНОПКИ ===
@bot.message_handler(func=lambda m: m.text == "🔍 Пошук птаха")
def btn_search(message): search(message)

@bot.message_handler(func=lambda m: m.text == "🎒 Інвентар")
def btn_inventory(message): inventory(message)

@bot.message_handler(func=lambda m: m.text == "🎪 Івент (Глушець)")
def btn_event(message): event(message)

@bot.message_handler(func=lambda m: m.text == "🐣 Івент (Пасха)")
def btn_easter(message): easter(message)

@bot.message_handler(func=lambda m: m.text == "🦅 Підтримка автора")
def btn_support(message):
    bot.send_message(message.chat.id,
        "🦅 *Підтримка автора*\n\n"
        "Підписуйся на TikTok канал автора про птахів України!\n\n"
        "👉 https://www.tiktok.com/@birdwatchingkremenets",
        parse_mode="Markdown"
    )

# === ОБРОБКА ПОМИЛОК ===
@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id,
        "❓ Невідома команда. Напиши /help щоб побачити список команд.")

# === FLASK (для Render 24/7) ===
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "🐦 UA Birds bot працює!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def safe_polling():
    while True:
        try:
            print("🐦 UA Birds bot запущено!")
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            print(f"❌ Помилка: {e}")
            time.sleep(5)

# Запускаємо Flask і бота паралельно
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

safe_polling()

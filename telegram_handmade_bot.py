import os
import sqlite3
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = '8420718991:AAFRWJOnXc-ZbTVH1SYHzZu1f_YEsMNxpi0'  # Токен от BotFather
ADMIN_CHAT = '@Gederim'  # твой Telegram username или числовой chat_id
DB = 'orders.db'
VIDEO_FILE_IDS = [
    'BAACAgUAAxkBAAM_aPxsCAmrWkJ58nmj3cRpw6bVpIMAAlIfAALbzsFXgHLU9QgxgMQ2BA',
    'BAACAgIAAxkBAAMsaPvlPks00YaqlzWAemnu63EEX-QAArZ5AAK2I9FLvjd1RmFWc582BA',
    'BAACAgIAAxkBAAMuaPvldzF4AZlYjnT83l5txR48Tl4AArl5AAK2I9FL5fPk4W_apS42BA'
]

PHOTO, CHILD_NAME, COMMENT, CONTACT = range(4)

TEXT = {
    'start_ru': "Здравствуйте! 👋\n"
                "Вы в боте Handmade Kids — здесь детские поделки оживают в короткие видео 🎬✨\n\n"
                "Пожалуйста, выберите действие:",
    'start_en': "Hello! 👋\n"
                "Welcome to Handmade Kids — here children's crafts come to life as short videos 🎬✨\n\n"
                "Please choose an action:",
    'choose_send_photo_ru': "Отправьте фото поделки (или напишите 'нет', чтобы пропустить).",
    'choose_send_photo_en': "Send a photo of the craft (or type 'no' to skip).",
    'ask_child_name_ru': "Как зовут ребёнка?",
    'ask_child_name_en': "What's the child's name?",
    'ask_comment_ru': "Короткий комментарий / пожелания:",
    'ask_comment_en': "Short comment / wishes:",
    'ask_contact_ru': "Оставьте контакт (Telegram или телефон):",
    'ask_contact_en': "Leave contact (Telegram or phone):",
    'thanks_ru': "Спасибо! Ваша заявка №{id} принята. Мы свяжемся с вами в Telegram.",
    'thanks_en': "Thanks! Your request #{id} is received. We'll contact you on Telegram.",
    'samples_ru': "Примеры наших работ:",
    'samples_en': "Samples of our works:",
    'lang_set_ru': "Язык установлен: русский.",
    'lang_set_en': "Language set: English.",
}

# ================== ИНИЦИАЛИЗАЦИЯ БД ==================
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            lang TEXT,
            item_photo_file_id TEXT,
            child_name TEXT,
            comment TEXT,
            contact TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ================== ХЕЛПЕР ==================
def t(key, lang):
    if lang == 'en':
        return TEXT.get(key + '_en', TEXT.get(key + '_ru'))
    return TEXT.get(key + '_ru')

# ================== КОМАНДЫ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton('🇷🇺 Русский'), KeyboardButton('🇬🇧 English')],
          [KeyboardButton('🖼️ Примеры работ / Samples'), KeyboardButton('✍️ Сделать заявку / Make a request')]]
    await update.message.reply_text(t('start_ru', 'ru'), reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if 'рус' in text or '🇷🇺' in text:
        context.user_data['lang'] = 'ru'
        await update.message.reply_text(t('lang_set', 'ru'))
        return
    if 'english' in text or '🇬🇧' in text:
        context.user_data['lang'] = 'en'
        await update.message.reply_text(t('lang_set', 'en'))
        return
    if 'пример' in text or 'samples' in text:
        await send_samples(update, context)
        return
    if 'сделать' in text or 'make a request' in text:
        await update.message.reply_text(t('choose_send_photo', context.user_data.get('lang', 'ru')))
        return PHOTO

async def send_samples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await update.message.reply_text(t('samples', lang))
    for fid in VIDEO_FILE_IDS:
        try:
            await context.application.bot.send_video(update.effective_chat.id, fid)
        except:
            pass

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id if update.message.photo else None
    context.user_data['item_photo_file_id'] = file_id
    await update.message.reply_text(t('ask_child_name', context.user_data.get('lang', 'ru')))
    return CHILD_NAME

async def child_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['child_name'] = update.message.text.strip()
    await update.message.reply_text(t('ask_comment', context.user_data.get('lang', 'ru')))
    return COMMENT

async def comment_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['comment'] = update.message.text.strip()
    await update.message.reply_text(t('ask_contact', context.user_data.get('lang', 'ru')))
    return CONTACT

async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()
    context.user_data['contact'] = contact
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('INSERT INTO orders (user_id, username, lang, item_photo_file_id, child_name, comment, contact) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (update.message.from_user.id, update.message.from_user.username or update.message.from_user.full_name, context.user_data.get('lang', 'ru'), context.user_data.get('item_photo_file_id'), context.user_data.get('child_name'), context.user_data.get('comment'), context.user_data.get('contact')))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    await update.message.reply_text(t('thanks', context.user_data.get('lang', 'ru')).format(id=order_id))
    note = f"Новая заявка #{order_id}\nОт: @{update.message.from_user.username or update.message.from_user.full_name}\nИмя ребёнка: {context.user_data.get('child_name')}\nКомментарий: {context.user_data.get('comment')}\nКонтакт: {context.user_data.get('contact')}\nUserID: {update.message.from_user.id}"
    if context.user_data.get('item_photo_file_id'):
        await context.application.bot.send_photo(ADMIN_CHAT, context.user_data.get('item_photo_file_id'), caption=note)
    else:
        await context.application.bot.send_message(ADMIN_CHAT, note)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Отменено.')
    return ConversationHandler.END

# ================== АВТО-ОБРАБОТКА FILE_ID ==================
async def auto_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        file_id = update.message.video.file_id
        await update.message.reply_text(f"File ID видео:\n{file_id}")
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"File ID фото:\n{file_id}")

# ================== MAIN ==================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Старт и конверсация
    app.add_handler(CommandHandler('start', start))
    conv = ConversationHandler(entry_points=[MessageHandler(filters.Regex('(?i)сделать заявку|make a request|✍️'), photo_received)],
                               states={PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
                                       CHILD_NAME: [MessageHandler(filters.TEXT, child_name_received)],
                                       COMMENT: [MessageHandler(filters.TEXT, comment_received)],
                                       CONTACT: [MessageHandler(filters.TEXT, contact_received)]},
                               fallbacks=[CommandHandler('cancel', cancel)])
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO, auto_file_id))

    print('Bot started...')
    app.run_polling()

if __name__ == '__main__':
    main()

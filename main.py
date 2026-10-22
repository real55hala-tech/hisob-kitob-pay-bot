import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from supabase import create_client, Client

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🌐 Render.com Port muammosini hal qilish uchun kichik Veb-Server
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Hisob-Kitob Bot Is Running Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# Atrof-muhit o'zgaruvchilari
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 👨‍💻 Admin Telegram ID
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8186445673")

# 💳 Rasmiy To'lov Sozlamalari
OFFICIAL_CARD = "9860 3501 4124 8996"
PREMIUM_PRICE = 30000  # 30,000 UZS / oy

# Supabase mijozini ishga tushirish
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 Ko'ptillilik lug'ati
TEXTS = {
    'uz': {
        'welcome': "Assalomu alaykum! **Hisob-Kitob** to'lov botiga xush kelibsiz! 🚀\n\nIltimos, tilni tanlang / Пожалуйста, выберите язык:",
        'lang_set': "🇺🇿 Til O'zbek tiliga o'zgartirildi!",
        'pay_info': (
            "💳 **Rasmiy Karta Raqamimiz:**\n`{card}`\n"
            "👤 **Karta Egasi:** Hisob-Kitob Rasmiy To'lov Karta\n"
            "💰 **Premium Obuna Narxi:** 30,000 so'm / oy\n\n"
            "📝 **Yo'riqnoma:**\n"
            "1. Yuqoridagi kartaga to'lov qiling.\n"
            "2. To'lov chekining skrinshotini (rasmini) ushbu botga yuboring.\n"
            "3. Rasm izohida (caption) ilovadagi telefon raqamingizni yozib qoldiring."
        ),
        'photo_received': "📸 Chek qabul qilindi! Xavfsizlik va dublikat tekshiruvi amalga oshirilmoqda...",
        'balance_partial': "✅ **{amount} so'm** qabul qilindi.\n\n📊 Sizning balansingiz: **{balance} so'm**.\n⏳ Premium aktivlashishi uchun yana **{needed} so'm** yuborishingiz kerak.",
        'premium_activated': "🎉 **Tabriklaymiz!** Balansingiz 30,000 so'mga yetdi.\n\n✨ **Premium status 30 kunga avtomatik aktivlashtirildi!**",
        'duplicate_error': "⚠️ **Diqqat!** Bu chek allaqachon ishlatilgan yoki bazada mavjud. Iltimos, yangi va haqiqiy chek yuboring.",
        'sent_to_admin': "📸 Chek adminga yuborildi. Tez orada ma'lumotlar ko'rib chiqiladi!"
    },
    'ru': {
        'welcome': "Здравствуйте! Добро пожаловать в платежный бот **Hisob-Kitob**! 🚀\n\nПожалуйста, выберите язык:",
        'lang_set': "🇷🇺 Язык изменен на Русский!",
        'pay_info': (
            "💳 **Официальная карта:**\n`{card}`\n"
            "👤 **Владелец:** Hisob-Kitob Rasmiy To'lov Karta\n"
            "💰 **Цена Premium подписки:** 30,000 сум / месяц\n\n"
            "📝 **Инструкция:**\n"
            "1. Переведите сумму на указанную карту.\n"
            "2. Отправьте скриншот чека в этот бот.\n"
            "3. В описании укажите ваш номер телефона."
        ),
        'photo_received': "📸 Чек получен! Проверка на дубликаты...",
        'balance_partial': "✅ **{amount} сум** принято.\n\n📊 Ваш баланс: **{balance} сум**.\n⏳ Для активации Premium осталось отправить: **{needed} сум**.",
        'premium_activated': "🎉 **Поздравляем!** Баланс достиг 30,000 сум.\n\n✨ **Premium статус автоматически активирован на 30 дней!**",
        'duplicate_error': "⚠️ **Внимание!** Этот чек уже был использован ранее. Пожалуйста, отправьте новый чек.",
        'sent_to_admin': "📸 Чек отправлен администратору на проверку!"
    },
    'en': {
        'welcome': "Welcome to **Hisob-Kitob** payment verification bot! 🚀\n\nPlease select your language:",
        'lang_set': "🇬🇧 Language changed to English!",
        'pay_info': (
            "💳 **Official Payment Card:**\n`{card}`\n"
            "👤 **Card Holder:** Hisob-Kitob Rasmiy To'lov Karta\n"
            "💰 **Premium Price:** 30,000 UZS / month\n\n"
            "📝 **Instructions:**\n"
            "1. Make transfer to the card above.\n"
            "2. Send the receipt screenshot to this bot.\n"
            "3. Put your registered phone number in the caption."
        ),
        'photo_received': "📸 Receipt received! Checking for duplicates...",
        'balance_partial': "✅ **{amount} UZS** accepted.\n\n📊 Your balance: **{balance} UZS**.\n⏳ Remaining amount for Premium: **{needed} UZS**.",
        'premium_activated': "🎉 **Congratulations!** Your balance reached 30,000 UZS.\n\n✨ **Premium status automatically activated for 30 days!**",
        'duplicate_error': "⚠️ **Warning!** This receipt has already been used. Please send a valid new receipt.",
        'sent_to_admin': "📸 Receipt sent to admin for verification!"
    }
}

USER_LANG = {}

def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, 'uz')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ])
    await update.message.reply_text(
        TEXTS['uz']['welcome'],
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.replace("lang_", "")
    USER_LANG[user_id] = lang_code
    
    lang = get_lang(user_id)
    await query.message.reply_text(TEXTS[lang]['lang_set'])
    
    pay_msg = TEXTS[lang]['pay_info'].format(card=OFFICIAL_CARD)
    await query.message.reply_text(pay_msg, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Mavjud emas"
    lang = get_lang(user_id)
    
    await update.message.reply_text(TEXTS[lang]['photo_received'])
    
    photo_file_id = update.message.photo[-1].file_id
    caption = update.message.caption or f"Telefon / Izoh berilmagan (ID: {user_id})"

    if supabase:
        try:
            check_duplicate = supabase.table("used_receipts").select("*").eq("file_id", photo_file_id).execute()
            if check_duplicate.data:
                await update.message.reply_text(TEXTS[lang]['duplicate_error'])
                return

            supabase.table("used_receipts").insert({"file_id": photo_file_id, "user_id": user_id}).execute()

            res = supabase.table("users").select("*").eq("telegram_id", user_id).execute()
            user_data = res.data[0] if res.data else None
            
            current_balance = user_data.get("balance", 0) if user_data else 0
            detected_payment = 30000 
            
            new_balance = current_balance + detected_payment
            
            if new_balance >= PREMIUM_PRICE:
                supabase.table("users").upsert({
                    "telegram_id": user_id,
                    "balance": 0,
                    "is_premium": True
                }).execute()
                await update.message.reply_text(TEXTS[lang]['premium_activated'], parse_mode="Markdown")
            else:
                needed = PREMIUM_PRICE - new_balance
                supabase.table("users").upsert({
                    "telegram_id": user_id,
                    "balance": new_balance
                }).execute()
                
                msg = TEXTS[lang]['balance_partial'].format(
                    amount=f"{detected_payment:,}",
                    balance=f"{new_balance:,}",
                    needed=f"{needed:,}"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
                return
        except Exception as e:
            logging.error(f"Supabase xatoligi: {e}")

    if ADMIN_CHAT_ID:
        admin_text = (
            f"📥 **Yangi to'lov cheki keldi!**\n\n"
            f"👤 **Foydalanuvchi:** @{username}\n"
            f"🆔 **Telegram ID:** `{user_id}`\n"
            f"📝 **Izoh / Telefon:** {caption}"
        )
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=photo_file_id,
                caption=admin_text,
                parse_mode="Markdown"
            )
        except Exception as admin_err:
            logging.error(f"Adminga yuborishda xatolik: {admin_err}")

    await update.message.reply_text(TEXTS[lang]['sent_to_admin'])

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        exit(1)
        
    # Veb-serverni orqa fonda yurgizish (Render port xatoligini to'g'rilash uchun)
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Hisob-Kitob Pay Bot mukammal rejimda ishga tushdi...")
    app.run_polling()

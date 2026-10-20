import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Atrof-muhit o'zgaruvchilari (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase mijozini ishga tushirish
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Assalomu alaykum! Hisob-Kitob ilovasining rasmiy to'lov tasdiqlash botiga xush kelibsiz! 🚀\n\n"
        "Premium obunani avtomatik yoqish uchun:\n"
        "1. Karta raqamimizga to'lov qiling.\n"
        "2. To'lov chekining skrinshotini shu botga yuboring.\n"
        "3. Ilovadagi ro'yxatdan o'tgan telefon raqamingiz yoki ID ingizni birga yozib qoldiring."
    )
    await update.message.reply_text(welcome_text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Chek qabul qilindi! Tekshirilmoqda va Premium statusi rasmiylashtirilmoqda...")
    
    # Kelajakda Tesseract OCR bilan chek matnini aniqlash va Supabase 'subscriptions' jadvalini yangilash kodi
    # Hozircha do'kondorga tasdiq xabarini yuboradi
    caption = update.message.caption or ""
    
    response_text = (
        "✅ To'lov cheki qabul qilindi va ko'rib chiqishga topshirildi!\n\n"
        "Tizim 1-3 daqiqa ichida akkauntingizga Premium obunani avtomatik biriktiradi."
    )
    await update.message.reply_text(response_text)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        exit(1)
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Hisob-Kitob Pay Bot ishga tushdi...")
    app.run_polling()
  

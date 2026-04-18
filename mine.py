import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv  # Библиотека для работы с .env
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. ЗАГРУЗКА НАСТРОЕК
load_dotenv() # Читаем файл .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Настройка нейросети
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Контекст (наша заглушка Айвазовского)
MOCK_ARTIST = {
    "medium": "Масло, холст",
    "style": "Романтизм, маринистика",
    "art_statement": "Я Иван Айвазовский. Моя жизнь — это море. Я стремлюсь запечатлеть бесконечную игру света на волнах."
}

# --- ПРОМПТЫ ---
ANALYSIS_PROMPT = "Ты экспертный арт-консультант. Опиши сюжет, цвета и атмосферу картины на фото. Будь краток (5 предложений)."
CREATIVE_PROMPT = "На основе анализа: {analysis}. Контекст художника: {statement}. Предложи 5 названий картины и 3 варианта поста для соцсетей."

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Секунду, смотрю на картину...")
    
    # Сохраняем фото
    photo_file = await update.message.photo[-1].get_file()
    photo_path = "temp_art.jpg"
    await photo_file.download_to_drive(photo_path)

    try:
        # Этап 1: Анализ фото
        with open(photo_path, "rb") as f:
            img_data = f.read()
        
        response_visual = model.generate_content([ANALYSIS_PROMPT, {"mime_type": "image/jpeg", "data": img_data}])
        
        # Этап 2: Текст
        final_prompt = CREATIVE_PROMPT.format(analysis=response_visual.text, statement=MOCK_ARTIST["art_statement"])
        response_text = model.generate_content(final_prompt)

        await update.message.reply_text(response_text.text)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Бот запущен! Иди в Телеграм и отправляй фото.")
    app.run_polling()

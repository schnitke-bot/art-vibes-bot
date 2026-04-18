import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
# Вставь свои ключи сюда
TELEGRAM_TOKEN = "ТВОЙ_ТЕЛЕГРАМ_ТОКЕН"
GEMINI_API_KEY = "ТВОЙ_GEMINI_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)
# Используем Flash-модель: она быстрая и хорошо "видит" детали на фото [cite: 123, 128]
model = genai.GenerativeModel('gemini-1.5-flash')

# Заглушка: данные художника (как будто он их уже ввел) 
MOCK_ARTIST_CONTEXT = {
    "medium": "Масло, холст",
    "style": "Романтизм, маринистика",
    "art_statement": "Я Иван Айвазовский. Моя жизнь — это море. Я стремлюсь запечатлеть бесконечную игру света на волнах, мощь стихии и поэзию морского горизонта[cite: 140, 145]."
}

# --- ПРОМПТЫ ---
# Шаг 1: Только факты и визуальный анализ [cite: 109, 110]
ANALYSIS_PROMPT = """
Ты — экспертный арт-консультант. Проведи глубокий визуальный анализ картины:
1. Сюжет и композиция: что в центре, какой ритм[cite: 110].
2. Цвет и свет: ключевые палитры и освещение[cite: 111].
3. Техника: учитывая медиум ({medium}) и стиль ({style}), опиши характер мазков[cite: 111].
4. Метафора: какую главную эмоцию передает работа[cite: 112].

Пиши профессионально, 5-6 предложений, без критики[cite: 113].
"""

# Шаг 2: Креатив на основе анализа и контекста художника [cite: 113, 115]
CREATIVE_PROMPT = """
Ты — креативный копирайтер. На основе анализа картины создай контент для соцсетей.
Контекст художника: {art_statement} [cite: 120]

ЗАДАЧА 1: Названия. Предложи 5 вариантов (Минимализм, Метафора, Атмосферное, Повествовательное, Абстрактное)[cite: 115, 116, 117].
ЗАДАЧА 2: Описания. Сгенерируй 3 варианта поста:
1. Поэтичный (чувства и смыслы)[cite: 118].
2. Экспертный (техника и свет)[cite: 119].
3. Story-style (интрига и вопрос к подписчикам)[cite: 120].
"""

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Изучаю вашу картину, секунду...")

    # 1. Скачиваем фото во временный файл
    photo_file = await update.message.photo[-1].get_file()
    photo_path = "temp_art.jpg"
    await photo_file.download_to_drive(photo_path)

    try:
        # --- ЭТАП 1: ВИЗУАЛЬНЫЙ АНАЛИЗ ---
        with open(photo_path, "rb") as f:
            image_data = f.read()
        
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        
        # Низкая температура для точности анализа (0.4) 
        analysis_resp = model.generate_content(
            [ANALYSIS_PROMPT.format(medium=MOCK_ARTIST_CONTEXT['medium'], style=MOCK_ARTIST_CONTEXT['style']), image_parts[0]],
            generation_config={"temperature": 0.4}
        )
        visual_analysis = analysis_resp.text

        # --- ЭТАП 2: ГЕНЕРАЦИЯ КОНТЕНТА ---
        # Высокая температура для креативности названий (0.9) [cite: 121, 147]
        creative_query = CREATIVE_PROMPT.format(art_statement=MOCK_ARTIST_CONTEXT['art_statement']) + f"\n\nАнализ картины: {visual_analysis}"
        
        creative_resp = model.generate_content(
            creative_query,
            generation_config={"temperature": 0.9}
        )

        # 4. Отправляем результат пользователю
        final_text = f"✨ **Варианты для вашей картины:**\n\n{creative_resp.text}"
        await update.message.reply_text(final_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка при анализе. Попробуйте еще раз.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Бот запущен и ждет картины...")
    app.run_polling()

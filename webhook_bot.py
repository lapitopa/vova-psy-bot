import os
import logging
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Должен быть https://<domain>/webhook

# Настройка GPT
openai.api_key = OPENAI_KEY

# Telegram приложение
application = ApplicationBuilder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    await update.message.reply_text("Я Вова. Пиши /analyze и мы начнём. Я тут.")

# Команда /analyze
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /analyze от пользователя {update.effective_user.id}")
    user_message = update.message.text.replace("/analyze", "").strip()
    if not user_message:
        await update.message.reply_text("Пиши, что у тебя внутри — я разложу по полочкам.")
        return

    prompt = f"""Ты психотерапевт. Проведи со мной сессию в стиле современного сочувствующего терапевта. Я сказал: "{user_message}""""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        reply = f"Что-то пошло не так: {e}"
        logger.error(f"Ошибка при запросе к OpenAI: {e}")

    await update.message.reply_text(reply)

# Добавление хендлеров
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("analyze", analyze_command))

# Запуск бота с webhook
if __name__ == "__main__":
    logger.info("Запуск бота с вебхуком...")
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=WEBHOOK_URL,
        url_path="webhook"  # Явно указываем путь вебхука
    )
    logger.info(f"Бот запущен с вебхуком на {WEBHOOK_URL}")

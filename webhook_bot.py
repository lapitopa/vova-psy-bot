import os
import openai
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_KEY

bot = Bot(token=TOKEN)
app = ApplicationBuilder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я Вова. Пиши /analyze и мы начнём. Я тут.")

# Команда /analyze
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.replace("/analyze", "").strip()
    if not user_message:
        await update.message.reply_text("Пиши, что у тебя внутри — я разложу по полочкам.")
        return

    prompt = (
        f"Ты психотерапевт. Проведи со мной психологическую беседу по методам РЭПТ и АСТ терапии.\n"
        f"Помоги мне справиться с моими эмоциями, страхами, разбери негативные убеждения и помоги мне вычислять когнитивные искажения.\n\n"
        f"Начни с того, чтобы уточнить мой запрос и главную проблему: {user_message}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    await update.message.reply_text(response['choices'][0]['message']['content'])

# Добавляем хендлеры
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("analyze", analyze_command))

# Aiohttp обработка
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await app.process_update(update)
    return web.Response()

# Настройка вебхука
async def on_startup(app_):
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    await app.initialize()

# Подключение маршрута
aio_app = web.Application()
aio_app.router.add_post(WEBHOOK_PATH, webhook_handler)
aio_app.on_startup.append(on_startup)

# Запуск
if __name__ == "__main__":
    web.run_app(aio_app, host="0.0.0.0", port=10000)
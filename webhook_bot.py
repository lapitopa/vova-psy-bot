import os
import openai
import asyncio
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()

# Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Инициализация
openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я Вова. Пиши /analyze и мы начнём. Я тут.")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.replace("/analyze", "").strip()
    if not user_message:
        await update.message.reply_text("Пиши, что у тебя внутри — я разложу по полочкам.")
        return

    prompt = (
        f"Ты психотерапевт. Проведи со мной психологическую беседу по методам РЭПТ и АСТ терапии.
"
        f"Помоги мне справиться с моими эмоциями, страхами, разбери негативные убеждения и помоги мне вычислять когнитивные искажения.

"
        f"Начни с того, чтобы уточнить мой запрос и главную проблему: {user_message}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    await update.message.reply_text(response['choices'][0]['message']['content'])

# Роуты и запуск
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("analyze", analyze_command))

async def handle(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return web.Response(text="ok")

async def main():
    await bot.initialize()
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    await application.initialize()
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle)
    web.run_app(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    asyncio.run(main())

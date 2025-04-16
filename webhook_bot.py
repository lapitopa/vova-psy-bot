import os
import openai
import asyncio
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# Загрузка переменных
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Настройка GPT
openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)

# Telegram приложение
application = ApplicationBuilder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я Вова. Пиши /analyze и мы начнём. Я тут.")

# Команда /analyze
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.replace("/analyze", "").strip()
    if not user_message:
        await update.message.reply_text("Пиши, что у тебя внутри — я разложу по полочкам.")
        return

    prompt = f"""Ты психотерапевт. Проведи со мной сессию в стиле современного сочувствующего терапевта. Я сказал: “{user_message}”"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        reply = f"Что-то пошло не так: {e}"

    await update.message.reply_text(reply)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("analyze", analyze_command))

async def main():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, application.webhook_handler())
    return app

if __name__ == "__main__":
    app = asyncio.run(main())
    web.run_app(app, host="0.0.0.0", port=10000)

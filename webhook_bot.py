import os
import logging
import random
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, filters
)

# Импорт других модулей проекта
from memory_manager import add_analysis, delete_user_memory, load_memory
from dialog_handler import start_dialog, handle_dialog_step, user_dialog_state
from keyboard_handler import get_main_keyboard

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Настройка OpenAI
client = OpenAI(api_key=OPENAI_KEY)

# Telegram приложение
application = ApplicationBuilder().token(TOKEN).build()

# Словарь для отслеживания состояния анализа пользователей
user_analysis_state = {}

# Модели для разных типов запросов
MODEL_SHORT = "gpt-3.5-turbo"
MODEL_ANALYSIS = "gpt-4"

# Генерация ответа через OpenAI
async def generate_response(prompt, temperature=0.88, max_tokens=250, model=MODEL_SHORT):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        fallback_responses = [
            "Что-то пошло не так. Давай попробуем еще раз?",
            "Мои нейроны временно перегрелись. Дай мне секунду.",
            "Упс, технические шумы. Можешь повторить?",
            "Извини, я отвлёкся. О чём мы говорили?",
            "Мозг завис. Перезагружаюсь..."
        ]
        return random.choice(fallback_responses)

# Меню команд
async def setup_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = [
        BotCommand("start", "Начать разговор с Вовой"),
        BotCommand("analyze", "Разбор по методу РЭПТ и АСТ терапии"),
        BotCommand("talk", "Терапевтично поболтать"),
        BotCommand("summary", "Личный анализ и направления роста"),
        BotCommand("clear", "Начать с чистого листа"),
        BotCommand("help", "Подсказка, кто такой Вова и как с ним общаться")
    ]
    await context.bot.set_my_commands(commands)

# Команды (start/help/analyze/talk/summary/clear/about) см. в предыдущем фрагменте
# Здесь оставим без повторов, если нужны — могу вставить ещё раз

# Обработка обычных сообщений и кнопок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    # Кнопки
    emoji_to_command = {
        "🧠 Анализ": analyze_command,
        "💬 Поговорить": talk_command,
        "📊 Выводы": summary_command,
        "🗑️ Очистить историю": clear_history_command
    }
    
    if message_text in emoji_to_command:
        await emoji_to_command[message_text](update, context)
        return

    # Если пользователь в процессе диалога или анализа
    if user_id in user_dialog_state:
        await handle_dialog_step(update, context)
    elif user_id in user_analysis_state:
        await analyze_command(update, context)
    else:
        # Если пользователь просто что-то написал без команды
        prompt = """Ты психотерапевт-бот по имени Вова в стиле @zapiskirizhego. Клиент отправил
        тебе сообщение без команды. Напиши короткий, прямолинейный ответ, в котором предложишь использовать команды /analyze или /talk."""
        suggestion = await generate_response(prompt, temperature=0.9, max_tokens=80)
        await update.message.reply_text(suggestion, reply_markup=get_main_keyboard())

# Регистрация обработчиков
def register_handlers():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("talk", talk_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("clear", clear_history_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск бота
if __name__ == "__main__":
    logger.info("Регистрация обработчиков команд...")
    register_handlers()

    logger.info("Запуск бота с вебхуком...")
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=WEBHOOK_URL,
        url_path="webhook"
    )

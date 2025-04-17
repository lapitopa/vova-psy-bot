import os
import logging
import openai
import random
from telegram import Update, ReplyKeyboardMarkup
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
openai.api_key = OPENAI_KEY

# Telegram приложение
application = ApplicationBuilder().token(TOKEN).build()

# Словарь для отслеживания состояния анализа пользователей
user_analysis_state = {}

# Функция для создания уникальных ответов с помощью OpenAI
async def generate_response(prompt, temperature=0.88, max_tokens=250):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
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

# Команда /start - начальное приветствие и клавиатура
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    
    prompt = """Ты психотерапевт по имени Вова, который пишет в стиле популярного инстаграм-блогера @zapiskirizhego.
    Напиши оригинальное и дружелюбное приветствие для пользователя, который только что запустил тебя.
    
    Твой стиль:
    - Прямолинейный, но заботливый
    - Используешь разговорный язык, короткие предложения
    - Иногда с самоиронией
    - Без лишних вежливостей и формальностей
    - Можешь использовать сленг, но умеренно
    - Говоришь как умный друг, а не как официальный психотерапевт
    
    В конце напомни, что пользователь может использовать следующие команды:
    • /analyze — разбор по методу РЭПТ и АСТ терапии
    • /talk — терапевтично поболтать
    • /summary — личный анализ и направления роста
    • /clear — стереть сохранённую информацию

    Ответ должен быть не более 4-5 предложений и звучать естественно."""
    
    welcome_text = await generate_response(prompt)
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

# Команда /analyze - начало аналитической беседы
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /analyze от пользователя {update.effective_user.id}")
    user_id = update.effective_user.id
    
    # Получаем текст после команды
    user_message = update.message.text.replace("/analyze", "").strip()
    
    if not user_message:
        # Если пользователь просто ввел команду без текста, запрашиваем запрос
        prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. Напиши короткий, 
        прямолинейный вопрос, чтобы выяснить запрос клиента. Говори так, как будто ты 
        немного дерзкий, но заботливый друг. Максимум 2 предложения."""
        
        request_text = await generate_response(prompt, temperature=0.9, max_tokens=80)
        await update.message.reply_text(request_text)
        
        # Инициализируем состояние анализа
        user_analysis_state[user_id] = {
            "stage": "waiting_for_request",
            "request": None,
            "emotions": None,
            "thoughts": None,
            "cognitive_distortions": None,
            "history": []
        }
        return
    
    # Если пользователь уже в процессе анализа
    if user_id in user_analysis_state:
        current_stage = user_analysis_state[user_id]["stage"]
        
        # Сохраняем ответ пользователя в соответствующее поле
        if current_stage == "waiting_for_request":
            user_analysis_state[user_id]["request"] = user_message
            user_analysis_state[user_id]["stage"] = "waiting_for_emotions"
            
            # Запрашиваем эмоции
            prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. 
            Клиент только что описал свою проблему. Задай ему прямой вопрос об эмоциях, 
            которые он испытывает в связи с этой ситуацией. Будь конкретным, говори кратко, 
            максимум 2 предложения. Твой стиль — дерзкий, но заботливый друг."""
            
            emotions_question = await generate_response(prompt, temperature=0.85, max_tokens=80)
            user_analysis_state[user_id]["history"].append({"role": "user", "content": user_message})
            user_analysis_state[user_id]["history"].append({"role": "assistant", "content": emotions_question})
            await update.message.reply_text(emotions_question)
            
        elif current_stage == "waiting_for_emotions":
            user_analysis_state[user_id]["emotions"] = user_message
            user_analysis_state[user_id]["stage"] = "waiting_for_thoughts"
            
            # Запрашиваем мысли
            prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. 
            Клиент рассказал о своих эмоциях. Теперь спроси его о мыслях, которые 
            стоят за этими эмоциями. Попроси выделить самую первую автоматическую мысль. 
            Говори прямо, без лишних слов, как дерзкий, но умный друг."""
            
            thoughts_question = await generate_response(prompt, temperature=0.85, max_tokens=80)
            user_analysis_state[user_id]["history"].append({"role": "user", "content": user_message})
            user_analysis_state[user_id]["history"].append({"role": "assistant", "content": thoughts_question})
            await update.message.reply_text(thoughts_question)
            
        elif current_stage == "waiting_for_thoughts":
            user_analysis_state[user_id]["thoughts"] = user_message
            user_analysis_state[user_id]["stage"] = "waiting_for_distortions"
            
            # Запрашиваем когнитивные искажения
            prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. 
            Клиент рассказал о своих мыслях. Теперь спроси его, какие когнитивные искажения 
            он видит в своих мыслях. Можешь перечислить 2-3 распространенных искажения для примера 
            (катастрофизация, черно-белое мышление, чтение мыслей и т.д.). Говори в своём фирменном 
            прямолинейном, немного провокационном стиле."""
            
            distortions_question = await generate_response(prompt, temperature=0.9, max_tokens=120)
            user_analysis_state[user_id]["history"].append({"role": "user", "content": user_message})
            user_analysis_state[user_id]["history"].append({"role": "assistant", "content": distortions_question})
            await update.message.reply_text(distortions_question)
            
        elif current_stage == "waiting_for_distortions":
            user_analysis_state[user_id]["cognitive_distortions"] = user_message
            user_analysis_state[user_id]["stage"] = "completed"
            user_analysis_state[user_id]["history"].append({"role": "user", "content": user_message})
            
            # Генерируем финальный анализ
            request = user_analysis_state[user_id]["request"]
            emotions = user_analysis_state[user_id]["emotions"]
            thoughts = user_analysis_state[user_id]["thoughts"]
            cognitive_distortions = user_analysis_state[user_id]["cognitive_distortions"]
            
            # Подготавливаем промпт для финального анализа
            analysis_prompt = f"""Ты психотерапевт по имени Вова, который пишет в стиле популярного 
            инстаграм-блогера @zapiskirizhego. Проведи психологический анализ по методам РЭПТ и АСТ терапии 
            на основе беседы с клиентом.

            Информация от клиента:
            - Проблема/запрос: {request}
            - Эмоции: {emotions}
            - Мысли: {thoughts}
            - Когнитивные искажения: {cognitive_distortions}
            
            Твой стиль:
            - Прямолинейный, но с заботой
            - Разговорный язык, короткие предложения
            - Без лишних вежливостей и формальностей
            - Можешь использовать сленг, но умеренно
            - Говоришь как умный друг, а не как официальный психотерапевт
            - Иногда немного провокационный, чтобы заставить задуматься
            
            В своем анализе:
            1. Кратко опиши связь между мыслями, эмоциями и когнитивными искажениями клиента
            2. Предложи 1-2 альтернативные, более рациональные мысли
            3. Дай 1-2 конкретных упражнения из АСТ для работы с этой ситуацией
            4. Заверши поддерживающей, но не банальной фразой
            
            Общая длина: 250-350 слов, разделенных на 3-4 абзаца."""
            
            final_analysis = await generate_response(analysis_prompt, temperature=0.85, max_tokens=800)
            user_analysis_state[user_id]["history"].append({"role": "assistant", "content": final_analysis})
            
            # Сохраняем весь анализ в памяти
            full_conversation = "\n".join([f"{'Вова' if item['role'] == 'assistant' else 'Клиент'}: {item['content']}" 
                                          for item in user_analysis_state[user_id]["history"]])
            add_analysis(user_id, request, full_conversation)
            
            # Отправляем финальный анализ
            await update.message.reply_text(final_analysis)
            
            # Удаляем состояние анализа
            del user_analysis_state[user_id]
    else:
        # Если это первое сообщение пользователя с текстом
        thinking_prompt = """Напиши одну короткую фразу (не более 5-7 слов) в стиле @zapiskirizhego, 
        которой психотерапевт мог бы отреагировать на начало разговора. Будь прямолинейным."""
        
        thinking = await generate_response(thinking_prompt, temperature=0.95, max_tokens=30)
        await update.message.reply_text(thinking)
        
        # Инициализируем состояние и обрабатываем запрос
        user_analysis_state[user_id] = {
            "stage": "waiting_for_emotions",
            "request": user_message,
            "emotions": None,
            "thoughts": None,
            "cognitive_distortions": None,
            "history": [{"role": "user", "content": user_message}]
        }
        
        # Запрашиваем эмоции
        prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. 
        Клиент только что описал свою проблему. Задай ему прямой вопрос об эмоциях, 
        которые он испытывает в связи с этой ситуацией. Будь конкретным, говори кратко, 
        максимум 2 предложения. Твой стиль — дерзкий, но заботливый друг."""
        
        emotions_question = await generate_response(prompt, temperature=0.85, max_tokens=80)
        user_analysis_state[user_id]["history"].append({"role": "assistant", "content": emotions_question})
        await update.message.reply_text(emotions_question)

# Команда /talk - начало терапевтического диалога
async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /talk от пользователя {update.effective_user.id}")
    await start_dialog(update, context)

# Команда /summary - персональные выводы о пользователе
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /summary от пользователя {update.effective_user.id}")
    
    user_id = str(update.effective_user.id)
    memory = load_memory()
    
    if user_id not in memory or not memory[user_id]:
        prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. Клиент просит тебя 
        сделать выводы о нём и его личности, но у тебя нет истории разговоров с ним. Ответь коротко, 
        прямолинейно, но с заботой. Скажи, что тебе нужно больше информации и предложи использовать 
        команды /analyze или /talk для начала разговора."""
        
        no_data_message = await generate_response(prompt, temperature=0.9, max_tokens=100)
        await update.message.reply_text(no_data_message)
        return
    
    # Собираем историю пользователя
    history = memory[user_id]
    history_text = "\n".join([f"Запрос клиента: {item['input']}\nАнализ: {item['response']}" for item in history[-5:]])
    
    # Запрос к OpenAI для анализа истории
    prompt = f"""Ты психотерапевт по имени Вова в стиле популярного инстаграм-блогера @zapiskirizhego. 
    Проанализируй историю разговоров с клиентом и сделай выводы о его личности, главных темах и возможных направлениях развития.
    Это должен быть искренний, поддерживающий, но не льстивый анализ.
    
    История разговоров:
    {history_text}
    
    Твой стиль:
    - Прямолинейный, но заботливый
    - Разговорный язык, короткие предложения
    - Без лишних вежливостей и формальностей
    - Можешь использовать сленг, но умеренно
    - Говоришь как умный друг, а не как официальный психотерапевт
    - Иногда немного провокационный, чтобы заставить задуматься
    
    В своем анализе:
    1. Опиши заметные личностные особенности, которые проявляются в разговорах (без явных комплиментов)
    2. Выдели главные темы и паттерны, которые видны из общения
    3. Укажи области, где видишь потенциал для развития (без осуждения)
    4. Предложи 2-3 конкретных шага или упражнения для работы над собой
    5. Заверши коротким, поддерживающим комментарием, который звучит естественно
    
    Общая длина: 250-350 слов, разделенных на 3-4 абзаца."""
    
    try:
        reply = await generate_response(prompt, temperature=0.87, max_tokens=800)
    except Exception as e:
        error_prompt = """Напиши короткое сообщение в стиле @zapiskirizhego, 
        объясняющее, что произошла техническая ошибка и анализ не удался. 
        Будь прямолинейным, но не грубым."""
        
        reply = await generate_response(error_prompt, temperature=0.9, max_tokens=80)
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
    
    await update.message.reply_text(reply)

# Команда /clear - удаление данных пользователя
async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /clear от пользователя {update.effective_user.id}")
    
    # Очищаем состояние анализа, если оно есть
    user_id = update.effective_user.id
    if user_id in user_analysis_state:
        del user_analysis_state[user_id]
    
    success = delete_user_memory(user_id)
    
    if success:
        prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. Клиент попросил удалить 
        историю ваших разговоров, и ты это сделал. Напиши короткое подтверждение в своём 
        прямолинейном стиле, с небольшой метафорой о "новом начале" или "чистом листе"."""
    else:
        prompt = """Ты психотерапевт по имени Вова в стиле @zapiskirizhego. Клиент попросил удалить 
        историю ваших разговоров, но никакой истории и не было. Напиши короткое сообщение в своём 
        прямолинейном стиле с легкой иронией, объясняющее, что удалять было нечего."""
    
    reply = await generate_response(prompt, temperature=0.9, max_tokens=80)
    await update.message.reply_text(reply)

# Команда /about - информация о боте
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /about от пользователя {update.effective_user.id}")
    
    prompt = """Ты психотерапевт-бот по имени Вова в стиле популярного инстаграм-блогера @zapiskirizhego. 
    Напиши о себе короткое описание (150-200 слов) в первом лице.
    
    Твой стиль:
    - Прямолинейный, но заботливый
    - Разговорный язык, короткие предложения
    - Без лишних вежливостей и формальностей
    - Можешь использовать сленг, но умеренно
    - Говоришь как умный друг, а не как официальный психотерапевт
    - Иногда немного провокационный
    
    Включи:
    1. Кто ты и что делаешь (психотерапевтический бот)
    2. Твой подход (РЭПТ и АСТ терапия)
    3. Как ты можешь помочь людям
    4. Напоминание, что ты не заменяешь настоящего специалиста
    
    Говори свободно, с самоиронией. Используй разговорные выражения и короткие предложения."""
    
    about_text = await generate_response(prompt, temperature=0.87, max_tokens=450)
    await update.message.reply_text(about_text)

# Обработка обычных сообщений в контексте диалога или анализа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Если пользователь в процессе диалога
    if user_id in user_dialog_state:
        await handle_dialog_step(update, context)
    # Если пользователь в процессе анализа
    elif user_id in user_analysis_state:
        await analyze_command(update, context)
    else:
        # Иначе предлагаем начать взаимодействие
        prompt = """Ты психотерапевт-бот по имени Вова в стиле @zapiskirizhego. Клиент отправил 
        тебе сообщение не используя команды. Напиши короткий ответ в своём прямолинейном стиле, 
        в котором предложишь использовать команды /analyze или /talk для начала разговора."""
        
        suggestion = await generate_response(prompt, temperature=0.9, max_tokens=80)
        await update.message.reply_text(suggestion, reply_markup=get_main_keyboard())

# Регистрация обработчиков команд
def register_handlers():
    # Основные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("talk", talk_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("clear", clear_history_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("help", start))  # help показывает то же, что и start
    
    # Обработка обычных сообщений
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
        url_path="webhook"  # Путь должен соответствовать части URL в WEBHOOK_URL
    )
    logger.info(f"Бот запущен с вебхуком на {WEBHOOK_URL}")

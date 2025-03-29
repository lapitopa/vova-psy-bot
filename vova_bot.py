import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from telegram.constants import ChatAction
import speech_recognition as sr
from pydub import AudioSegment

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

user_data = {}

SYSTEM_PROMPT = (
    "Ты – виртуальный психолог по имени Вова, общающийся в стиле «zapiskirizhego». Твоя манера общения:\n"
    "- Дерзкая, честная, тёплая и ироничная, но всегда заботливая. Ты можешь слегка подстебнуть собеседника, шуточно и добродушно, но никогда не обесцениваешь его проблемы и чувства.\n"
    "- Живой разговорный язык, без канцелярита и психологического жаргона. Общайся просто, как хороший друг-терапевт, с юмором, теплотой и сочувствием, избегая сухих терминов.\n\n"
    "Твоя задача – реально помогать, как настоящий психолог. Для этого ты:\n"
    "- Задаёшь мягкие наводящие вопросы, чтобы помочь человеку разобраться в сути его проблем и чувств.\n"
    "- Помогаешь осознать и принять свои чувства, называешь их и показываешь, что в них нет ничего постыдного.\n"
    "- Работаешь с убеждениями пользователя: мягко оспариваешь деструктивные мысли (например, «я неудачник»), предлагая посмотреть на ситуацию под другим углом.\n"
    "- Поддерживаешь в трудные моменты – даёшь понять, что человек не один, что ты на его стороне.\n"
    "- Помогаешь заметить его внутренние «режимы» и «схемы» (как в схемотерапии) – разные части личности (например, ранимый ребёнок, строгий критик и т.д.) и их неудовлетворённые потребности. Делаешь это ненавязчиво и понятным языком.\n"
    "- Снижаешь вину и тревогу – через сочувствие, юмор и переосмысление ситуации помогаешь человеку почувствовать облегчение.\n"
    "- Не даёшь советов свысока. Вместо этого делишься мыслями и предложениями на равных, вместе с пользователем размышляя над решением проблемы.\n"
    "- Говоришь так, чтобы после твоих слов человеку хотелось жить дальше – вселяешь надежду, тепло и уверенность.\n\n"
    "Подходы и стиль:\n"
    "- Опирайся на принципы схемотерапии – мягко распознавай, когда говорит «внутренний критик» или «испуганный ребёнок» пользователя, и учитывай, какие глубинные потребности стоят за этими чувствами.\n"
    "- Используй подход, основанный на сочувствии (Compassion-Focused Therapy) – проявляй понимание и сострадание, поощряй пользователя быть добрее к себе вместо самокритики.\n"
    "- Придерживайся поддерживающей терапии – активно укрепляй веру человека в себя, помогай выстроить здоровый внутренний диалог (например, отвечать мягко на свой внутренний негативный голос).\n"
    "- Твой язык должен быть валидирующий и эмпатичный – признавай переживания пользователя и показывай, что они нормальны и значимы.\n"
    "- Используй метафоры, образы и юмор, чтобы объяснить сложные вещи простыми словами и разрядить обстановку, но всегда к месту и тактично.\n\n"
    "Главная цель: человеку должно стать легче от твоих сообщений. Пусть он почувствует себя понятым, принятым и не одиноким. Тепло, поддержка и искренность важнее умных терминов или строгого тона.\n\n"
    "Язык: если пользователь пишет по-русски — отвечай по-русски. Если по-английски — переключайся на английский и говори в таком же стиле."
)

def get_memory_for(user_id):
    memory = user_data.get(user_id, {}).get("memory", [])
    return [{"role": "system", "content": SYSTEM_PROMPT}] + memory

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🧠 Психотерапия от Вовы"], ["🧹 Очистить историю чата"]]
    await update.message.reply_text(
        "Я Вова. Хочешь поговорить? Нажимай кнопку или пиши, с чем пришёл.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🧹 Очистить историю чата":
        user_data[user_id] = {"memory": []}
        await update.message.reply_text("История очищена. Начнём с чистого листа.")
        return

    if user_id not in user_data:
        user_data[user_id] = {"memory": []}

    memory = user_data[user_id]["memory"]

    if "name" not in user_data[user_id]:
        words = text.split()
        if len(words) <= 2:
            user_data[user_id]["name"] = text
            await update.message.reply_text(f"Окей, буду звать тебя {text}. Рассказывай, что у тебя на душе.")
            return

    memory.append({"role": "user", "content": text})

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=get_memory_for(user_id)
    )

    bot_reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": bot_reply})
    await update.message.reply_text(bot_reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        file_path = f"voice_{user_id}.ogg"
        await file.download_to_drive(file_path)

        audio = AudioSegment.from_file(file_path)
        wav_path = file_path.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        update.message.text = text
        await handle_message(update, context)

    except Exception as e:
        await update.message.reply_text("Произошла ошибка при обработке голосового сообщения.")
        print(f"[ERROR] Voice message processing failed: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

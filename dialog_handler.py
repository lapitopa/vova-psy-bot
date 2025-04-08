
from telegram import Update
from telegram.ext import ContextTypes

# Храним диалоговые состояния пользователей
user_dialog_state = {}

# Вопросы от Вовы — в стиле дерзкого, но заботливого друга
dialog_questions = [
    "Окей. Что у тебя там случилось?",
    "А что ты чувствуешь в теле, когда об этом думаешь?",
    "Какая мысль пронеслась первой? Даже если она кажется глупой.",
    "Если бы это была фраза, которую ты говоришь себе — как бы она звучала?",
    "А теперь представь, что это говорит внутренний критик. Что он орёт тебе в голову?",
    "Что бы ты сказала подруге, если бы она была в такой же ситуации?",
    "Что ты можешь сделать прямо сейчас, чтобы быть к себе помягче?"
]

async def start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_dialog_state[user_id] = 0

    await update.message.reply_text("Давай, начнём. Я буду задавать тебе вопросы один за другим. Ты пиши — я слушаю.")
    await update.message.reply_text(dialog_questions[0])

async def handle_dialog_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_dialog_state:
        return  # пользователь не начал беседу

    step = user_dialog_state[user_id] + 1

    if step < len(dialog_questions):
        user_dialog_state[user_id] = step
        await update.message.reply_text(dialog_questions[step])
    else:
        del user_dialog_state[user_id]
        await update.message.reply_text("Спасибо, что рассказала. Ты держишься — и я это вижу. Можешь просто остаться здесь и быть собой.")

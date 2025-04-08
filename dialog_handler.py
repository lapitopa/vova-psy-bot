
from telegram import Update
from telegram.ext import ContextTypes

# Храним диалоговые состояния пользователей
user_dialog_state = {}

# Вопросы для пошаговой беседы
dialog_questions = [
    "Окей. Что с тобой сейчас происходит? Опиши это в паре предложений.",
    "А что ты чувствуешь в теле, когда об этом думаешь?",
    "Какая мысль приходит первой в голову, когда ты это переживаешь?",
    "Если бы эта мысль была фразой, которую ты говоришь себе — как бы она звучала?",
    "А если представить, что это говорит твой внутренний критик — что бы он тебе сказал?",
    "Теперь скажи: а что бы ты сказала подруге, если бы она оказалась в такой ситуации?",
    "Что ты можешь сделать, чтобы быть к себе мягче прямо сейчас?",
]

async def start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_dialog_state[user_id] = 0

    await update.message.reply_text("Начнём. Я буду задавать тебе вопросы один за другим. Пиши честно, ок?")
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
        await update.message.reply_text("Спасибо, что прошла это со мной. Ты большая умница. Хочешь — можешь написать ещё, я рядом.")

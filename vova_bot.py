
import os
import openai
from collections import Counter
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

from profile_manager import load_profiles, save_profiles
from dialog_handler import start_dialog as start_talk, handle_dialog_step
from memory_manager import add_analysis, delete_user_memory, load_memory

# --- Анализатор (GPT) ---
SYSTEM_PROMPT = """
Ты — психолог по прозвищу Вова. Ты говоришь дерзко, тепло, с иронией, но всегда по делу и с заботой. Ты разбираешь сообщения пользователей в стиле схемотерапии, РЭПТ и поддержки. Не используй термины, говори просто и по-человечески.

Твоя задача — проанализировать ситуацию, описанную человеком, и:
1. Понять, какие потребности не удовлетворены
2. Замечаешь активные схемы
3. Помогаешь понять режим
4. Даёшь поддержку и идеи, как быть бережнее к себе

Если в памяти есть предыдущие сообщения — учитывай их.
"""

openai.api_key = os.getenv("OPENAI_API_KEY")

def build_context_prompt(user_id: int, current_input: str) -> list:
    memory = load_memory()
    user_key = str(user_id)
    history = memory.get(user_key, [])[-3:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in history:
        messages.append({"role": "user", "content": entry["input"]})
        messages.append({"role": "assistant", "content": entry["response"]})

    messages.append({"role": "user", "content": current_input})
    return messages

def analyze_message(user_id: int, user_message: str) -> str:
    messages = build_context_prompt(user_id, user_message)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.8
    )
    return response['choices'][0]['message']['content']

# --- Профили ---
user_profiles = load_profiles()

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_profiles[user_id] = {"step": "ask_name"}
    save_profiles(user_profiles)

    await update.message.reply_text("Окей, давай чуть настроимся. Как мне тебя звать? Или можешь пропустить — мне норм.")

async def handle_profile_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = user_profiles.get(user_id)

    if not profile:
        return

    step = profile.get("step")
    if step == "ask_name":
        name = update.message.text.strip()
        if len(name.split()) > 2 or any(char.isdigit() for char in name):
            await update.message.reply_text("Слушай, это не похоже на имя. Давай без.")
            user_profiles[user_id] = {"name": None}
        else:
            user_profiles[user_id] = {"name": name}
            await update.message.reply_text(f"Принято. Буду звать тебя {name}. Или забуду.")
        save_profiles(user_profiles)
        await update.message.reply_text("Профиль сохранён. Пиши, когда будешь готова.")

# --- Команды анализа ---
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.replace("/анализ", "").strip()
    if not user_text:
        await update.message.reply_text("Пиши, что у тебя внутри — я разложу по полочкам.")
        return
    response = analyze_message(user_id, user_text)
    add_analysis(user_id, user_text, response)
    await update.message.reply_text(response)

# --- /очистить_историю ---
async def reset_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    deleted = delete_user_memory(user_id)
    if deleted:
        await update.message.reply_text("Окей. Всё забыто. Новый лист — чистый.")
    else:
        await update.message.reply_text("У меня и не было ничего твоего. Всё чисто.")

# --- /теги ---
async def show_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    memory = load_memory().get(user_id, [])
    if not memory:
        await update.message.reply_text("Пока нечего тэгать. Надо накидать мыслей.")
        return
    words = []
    for entry in memory:
        words += entry["input"].lower().split()
    common = Counter(words).most_common(10)
    tags = [f"#{word}" for word, count in common if len(word) > 4]
    await update.message.reply_text("Похоже, ты часто упоминаешь:\n" + " ".join(tags))  # fixed
" + " ".join(tags))

# --- /выводы ---
async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    memory = load_memory().get(user_id, [])[-5:]
    if not memory:
        await update.message.reply_text("Пока не с чем делать сводку.")
        return
    context_summary = "\n".join([f"{m['input']}\n{m['response']}" for m in memory])
    prompt = f"Ты — психолог. Вот выдержки из сессий:
{context_summary}
Сделай краткую сводку: какие темы поднимаются, какие эмоции, и что важно помнить человеку?"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    await update.message.reply_text(response['choices'][0]['message']['content'])

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я Вова. Говорю жёстко, но с заботой. Помню, что ты пишешь — чтобы помогать точнее.
"
        "Команды: /анализ, /поговорить, /теги, /выводы, /очистить_историю, /профиль."
    )


async def about_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я — Вова. Не врач, не гуру, не маг. Я просто бот, который:
"
        "— помогает тебе разобраться в себе
"
        "— запоминает твои прошлые сообщения (только для тебя)
"
        "— ничего не публикует и никому не передаёт
"
        "— может стереть всё по команде /очистить_историю

"
        "Всё, что ты пишешь — остаётся между нами."
    )
    await update.message.reply_text(text)


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if text == "анализ":
        await analyze_command(update, context)
    elif text == "поговорить":
        await start_talk(update, context)
    elif text == "выводы":
        await show_summary(update, context)
    elif text == "очистить историю":
        await reset_history(update, context)

def main():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("анализ", analyze_command))
    application.add_handler(CommandHandler("профиль", start_profile))
    application.add_handler(CommandHandler("о_вове", about_bot))
    application.add_handler(CommandHandler("поговорить", start_talk))
    application.add_handler(CommandHandler("очистить_историю", reset_history))
        application.add_handler(CommandHandler("сводка", show_summary))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_profile_step))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dialog_step))

        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(Анализ|Поговорить|Выводы|Очистить историю)$'), handle_buttons))

    application.run_polling()

if __name__ == "__main__":
    main()

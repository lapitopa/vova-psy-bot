from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            ["🧠 Анализ", "💬 Поговорить"],
            ["📊 Выводы", "🗑️ Очистить историю"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

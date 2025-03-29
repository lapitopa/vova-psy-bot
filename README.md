# Vova Psy Bot

Vova — это Telegram-бот в стиле zapiskirizhego. Он:
- ведёт диалог как дерзкий, ироничный, но заботливый психолог,
- использует подходы схемотерапии и CFT, но без канцелярита,
- запоминает историю пользователя,
- умеет очищать историю,
- может работать с голосовыми сообщениями (если активированы).

## Развёртывание на Render

1. Зарегистрируйся на https://render.com
2. Создай новый Web Service
3. Подключи GitHub-репозиторий с этим проектом
4. Укажи:
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python vova_bot.py`
5. В секции Environment Variables добавь переменные:
   - `TELEGRAM_TOKEN`
   - `OPENAI_API_KEY`

Готово!
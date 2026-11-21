# ⚡ Linear Inbox Telegram Bot

Швидкий кишеньковий бот для розробника: записуйте ідеї, задачі або баг-репорти на ходу прямо в **Linear** ([linear.app](https://linear.app)).

## 🚀 Як це працює:
1. Ви надсилаєте боту в Telegram звичайне повідомлення або фото зі скріншотом:
   > *«додати звук кипіння лави при наближенні»*
2. Бот показує інлайн-кнопки з усіма вашими активними проєктами в Linear:
   - `[ 🏔️ Break the Mountain ]`
   - `[ 🎮 ClassicPlayBot ]`
   - `[ 🎬 The Horror Set ]`
   - `[ 🌐 MyshCode Studio ]`
   - `[ 📥 Тільки Inbox ]`
3. Натискаєте кнопку — таска миттєво створюється в Linear і повертає вам посилання на картку!

---

## 🛠️ Налаштування за 2 хвилини:

### 1. Отримати токен Telegram бота
- Відкрийте [@BotFather](https://t.me/BotFather) у Telegram.
- Напишіть `/newbot`, оберіть назву (наприклад, `MyshCode Linear Bot`) та юзернейм (наприклад, `myshcode_linear_bot`).
- Скопіюйте отриманий токен.

### 2. Отримати API-ключ у Linear
- Зайдіть у [Linear](https://linear.app) ➔ натисніть на аватар/назву воркспейсу ліворуч зверху.
- Перейдіть у **Settings** ➔ **My Account** ➔ **Security & Access** ➔ розділ **Personal API keys** (або пряме посилання: `linear.app/YOUR_WORKSPACE/settings/api`).
- Натисніть **Create key**, назвіть його `Telegram Bot` і скопіюйте ключ (починається з `lin_api_...`).

### 3. Дізнатися свій Telegram User ID (для захисту)
- Напишіть боту [@userinfobot](https://t.me/userinfobot) і скопіюйте ваш числовий Id (наприклад, `123456789`).

### 4. Налаштувати `.env`
Створіть файл `.env` поруч із файлом `.env.example`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxx
ALLOWED_USER_IDS=123456789
```

---

## 💻 Локальний запуск:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python bot.py
```

## 🐳 Запуск у Docker (на сервері Oracle):
```bash
docker compose up -d --build
```
*(Споживає всього ~15–20 МБ оперативної пам'яті)*.

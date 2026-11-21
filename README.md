# ⚡ Linear Telegram Inbox Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-009dc4.svg)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, developer-first Telegram bot that instantly captures ideas, bug reports, and tasks directly into your [Linear](https://linear.app) workspace with dynamic inline project routing.

---

## 🎯 How It Works

1. Send any quick thought, forwarded message, or screenshot to your private Telegram bot:
   > *"Add particle effects on player jump"*
2. The bot fetches your active workspace projects via Linear's GraphQL API and presents an interactive inline menu:
   - `[ 📱 Mobile App ]`
   - `[ 🌐 Web Platform ]`
   - `[ 🎮 Game Client ]`
   - `[ 🛠️ Backend API ]`
   - `[ 📥 General Inbox ]`
3. Tap the target project with one thumb — the issue is **immediately created in Linear** and returns a direct issue link (e.g. `[ENG-42]`).

---

## ✨ Features

- **Dynamic Project Discovery:** Automatically queries active Linear projects and teams on startup and on `/reload`.
- **Photo & Screenshot Support:** Send bug screenshots directly from mobile; the bot notes media attachments in the task description.
- **Access Control:** Restrict bot usage strictly to your Telegram User ID (`ALLOWED_USER_IDS`) to prevent unauthorized entries.
- **Ultra Lightweight:** Clean async code (`aiogram 3` + `httpx`), consumes only ~15–20 MB of RAM in Docker.

---

## 🛠️ Quick Setup (2 Minutes)

### 1. Telegram Bot Token
1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`, choose a name (e.g., `My Linear Inbox`) and username (e.g., `my_linear_inbox_bot`).
3. Copy the HTTP API token.

### 2. Linear Personal API Key
1. Go to [Linear Settings](https://linear.app) ➔ **My Account** ➔ **Security & Access**.
2. Scroll to **Personal API keys** ➔ Click **Create key**.
3. Name it `Telegram Inbox` and copy the generated token (`lin_api_...`).

### 3. Your Telegram User ID (Optional Security)
1. Send any message to [@userinfobot](https://t.me/userinfobot) to get your numeric Telegram ID (e.g., `123456789`).

### 4. Configuration
Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxx
ALLOWED_USER_IDS=123456789
```

---

## 🚀 Running the Bot

### Option A: Local Python
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the bot
python main.py
```

### Option B: Docker Compose (Recommended for VPS / Oracle Cloud)
```bash
docker compose up -d --build
```

To view logs:
```bash
docker compose logs -f
```

---

## ⌨️ Bot Commands

- `/start` — View connection status, teams, and active Linear projects.
- `/reload` — Refresh teams and projects cache from Linear API without restarting.

---

## 📄 License

MIT License. Free to use, modify, and distribute.

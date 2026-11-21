# ⚡ Linear Telegram Inbox Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-009dc4.svg)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)](https://www.docker.com/)
[![Gemini Flash](https://img.shields.io/badge/AI-Gemini%20Flash-8e44ad.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A smart, lightweight Telegram bot that captures ideas, bug reports, and voice memos directly into your [Linear](https://linear.app) workspace with AI structuring and one-tap project routing.

---

## 🎯 How It Works

1. **Send anything to the bot:**
   - 🎙 **Voice note:** *"Record a quick memo while on the go"*
   - 💬 **Text thought:** *"Fix sticky header jitter on mobile Safari"*
   - 📸 **Screenshot:** Bug picture with or without a caption
2. **AI Structuring & Review (Gemini Flash):**
   - Transcribes audio natively with high accuracy (Ukrainian & English).
   - Generates an actionable title, context, acceptance criteria, and priority level (`P0`–`P3`).
   - Presents an interactive preview:
     - `[ 📁 Choose Project & Save ]`
     - `[ 🔄 Regenerate ]`
     - `[ 📝 Save as Raw Text ]`
     - `[ ❌ Cancel ]`
3. **One-tap Linear routing:**
   - Tap your target Linear project — the issue is instantly created in Linear and returns a direct issue link (e.g. `[ENG-42]`).

---

## ✨ Features

- **🎙 Voice Message Transcription:** Natively transcribes `.ogg` voice notes via Gemini Flash without ffmpeg or local Whisper overhead.
- **🤖 AI Task Structuring:** Turns rambling thoughts or bullet points into clear Linear tasks with context and acceptance criteria.
- **⚙️ Full Control (`/settings`):** Toggle AI formatting ON/OFF or switch between Ukrainian 🇺🇦 and English 🇬🇧 at any time.
- **Dynamic Project Discovery:** Automatically queries active Linear projects and teams on startup and on `/reload`.
- **Photo & Screenshot Support:** Attaches notes for screenshots sent directly from mobile.
- **Strict Access Control:** Restrict bot usage strictly to your Telegram User ID (`ALLOWED_USER_IDS`).
- **Persistent Settings:** Remembers your AI & language preferences in persistent storage (`data/settings.json`).
- **Ultra Lightweight:** Modular async architecture (`aiogram 3` + `httpx`), uses only ~25 MB RAM in Docker.

---

## 🛠️ Quick Setup (2 Minutes)

### 1. Telegram Bot Token
1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`, choose a name and username.
3. Copy the HTTP API token.

### 2. Linear Personal API Key
1. Go to [Linear Settings](https://linear.app) ➔ **Security & access** ➔ **Personal API keys**.
2. Click **Create key**, name it `Telegram Inbox` and copy the generated token (`lin_api_...`).

### 3. Google Gemini API Key (For Voice & AI Structuring)
1. Get a free API key at [Google AI Studio](https://aistudio.google.com/).
2. Copy the API key. *(Optional: bot runs in raw mode if key is omitted).*

### 4. Configuration
Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxx
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

### Option B: Docker Compose (Recommended)
```bash
docker compose up -d --build
```

View live logs:
```bash
docker compose logs -f
```

---

## ⌨️ Bot Commands

- `/start` — View connection status, teams, active projects, and AI mode.
- `/settings` — Toggle AI structuring ON/OFF and switch language (UA / EN).
- `/reload` — Refresh teams and projects cache from Linear API without restarting.

---

## 📄 License

MIT License. Free to use, modify, and distribute.

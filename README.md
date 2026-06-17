# Telegram Image Generation Bot (NVIDIA API)

This is a lightweight Python Telegram Bot that generates images from user text prompts using NVIDIA's serverless Image Generation API (e.g. FLUX.1-schnell or Stable Diffusion 3.5 Large).

## Features
- **Prompt to Image:** Enter any text prompt (e.g. "A majestic eagle flying over snow-covered mountains, oil painting") and get a 1024x1024 image back.
- **Visual Feedback:** Shows a status message ("Generating your image...") and typing/upload indicators while the image is rendering.
- **Robust Endpoint Support:** Handles both base64 JSON responses and image URLs automatically.
- **Configurable Models:** Swappable model configurations via environment variables.

---

## Prerequisites

To run this bot, you will need:
1. **Python 3.10+** installed on your system.
2. **Telegram Bot Token:**
   - Open Telegram and message [@BotFather](https://t.me/BotFather).
   - Send the command `/newbot` and follow the prompts.
   - Copy the HTTP API token generated for you.
3. **NVIDIA API Key:**
   - Sign up at the [NVIDIA API Catalog](https://build.nvidia.com/).
   - Search for a visual generative model (e.g. `FLUX.1-schnell`).
   - Click **Get API Key** and copy the token (starts with `nvapi-`).

---

## Setup & Run Instructions

### 1. Clone or Open the Workspace
Ensure you are in the project folder:
```bash
cd "d:/github projects/telegram chat bot (image)"
```

### 2. Configure Environment Variables
Create a file named `.env` in the root folder and copy the contents of `.env.template` into it. Fill in your tokens:
```ini
TELEGRAM_BOT_TOKEN=your_real_telegram_bot_token
NVIDIA_API_KEY=nvapi-your_real_nvidia_api_key
```

### 3. Create a Python Virtual Environment
Run the following commands in your terminal to set up a virtual environment and install dependencies:

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Bot
To start the bot, run:
```bash
python bot.py
```

You should see log messages indicating the bot is starting:
```text
🚀 NVIDIA Image Gen Bot is active!
👉 Model: black-forest-labs/flux-1-schnell
👉 API URL: https://integrate.api.nvidia.com/v1/images/generations
Press Ctrl+C to stop.
```

---

## Customizing the Model
To change the image generation model (e.g. to run `stabilityai/stable-diffusion-3.5-large`), simply update the keys in your `.env` file:
```ini
# For Stable Diffusion 3.5 Large
NVIDIA_MODEL=stabilityai/stable-diffusion-3.5-large
```
Make sure the model you choose is available in the NVIDIA catalog and supports the OpenAI-compatible `/v1/images/generations` path.

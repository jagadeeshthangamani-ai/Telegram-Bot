import os
import io
import base64
import logging
import requests
from dotenv import load_dotenv
import telebot

# Set up logging format
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve configurations
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_URL = os.getenv("NVIDIA_API_URL", "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "black-forest-labs/flux.1-schnell")
NVIDIA_STEPS = int(os.getenv("NVIDIA_STEPS", "2" if "schnell" in NVIDIA_MODEL.lower() else "25"))

# Validate required configuration
missing_vars = []
if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
    missing_vars.append("TELEGRAM_BOT_TOKEN")
if not NVIDIA_API_KEY or NVIDIA_API_KEY == "nvapi-your_nvidia_api_key_here":
    missing_vars.append("NVIDIA_API_KEY")

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    print("\n" + "="*60)
    print("ERROR: Missing configuration!")
    print("Please create a '.env' file in the root directory based on '.env.template'")
    print(f"and configure the following values: {', '.join(missing_vars)}")
    print("="*60 + "\n")
    exit(1)

# Initialize the Telegram Bot and fetch bot info
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
try:
    bot_info = bot.get_me()
    BOT_USERNAME = bot_info.username
    logger.info(f"Bot successfully authorized. Username: @{BOT_USERNAME}")
except Exception as auth_err:
    logger.error(f"Failed to fetch bot username: {auth_err}")
    BOT_USERNAME = "NvidiaImageGenBot"

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """Sends a friendly welcoming message to the user."""
    welcome_text = (
        "🤖 *Welcome to the NVIDIA Image Generation Bot!*\n\n"
        "You can use me to generate images using NVIDIA's serverless AI endpoints.\n\n"
        "💬 *How to use me:*\n"
        "• *In Private DM:* Just send me any text description directly.\n"
        f"• *In Groups:* Use the `/generate` or `/gen` command followed by your prompt, or mention me directly:\n"
        f"  `/generate a futuristic city` or `@{BOT_USERNAME} a futuristic city`\n\n"
        f"🎨 *Current Model:* `{NVIDIA_MODEL}`\n\n"
        "Just send a prompt or command to get started!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

def process_image_generation(message, prompt):
    """Handles the actual calling of the NVIDIA API and sending the response."""
    prompt = prompt.strip()
    if not prompt:
        return

    # Send an initial response to let the user know we are working on it
    try:
        status_msg = bot.reply_to(
            message, 
            "🎨 *Generating your image... please wait a moment.*", 
            parse_mode="Markdown"
        )
    except Exception:
        try:
            status_msg = bot.send_message(
                message.chat.id,
                "🎨 *Generating your image... please wait a moment.*",
                parse_mode="Markdown"
            )
        except Exception as send_err:
            logger.error(f"Failed to send status message: {send_err}")
            return

    try:
        # Show a "sending photo" action to indicate activity
        bot.send_chat_action(message.chat.id, "upload_photo")

        # Set up request details
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Build the payload dynamically based on the URL type
        # NVIDIA GenAI direct endpoints (e.g. ai.api.nvidia.com/v1/genai/...) do not accept fields like n, size, model, response_format
        if "/genai/" in NVIDIA_API_URL:
            payload = {
                "prompt": prompt,
                "seed": 0,
                "steps": NVIDIA_STEPS
            }
            logger.info(f"Sending direct GenAI request to: {NVIDIA_API_URL}. Steps: {NVIDIA_STEPS}. Prompt: '{prompt}'")
        else:
            payload = {
                "prompt": prompt,
                "model": NVIDIA_MODEL,
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json"
            }
            logger.info(f"Sending OpenAI-compatible request to: {NVIDIA_API_URL}. Model: {NVIDIA_MODEL}. Prompt: '{prompt}'")
        
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
        
        # If the request fails, raise HTTPError
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                if "detail" in error_json:
                    error_detail = error_json["detail"]
                elif "message" in error_json:
                    error_detail = error_json["message"]
            except Exception:
                pass
            raise Exception(f"NVIDIA API Error (HTTP {response.status_code}): {error_detail}")

        # Parse response JSON
        resp_data = response.json()
        image_bytes = None
        
        # 1. Check for NVIDIA GenAI response format: 'artifacts' list containing 'base64'
        if "artifacts" in resp_data and resp_data["artifacts"]:
            image_entry = resp_data["artifacts"][0]
            if "base64" in image_entry:
                b64_data = image_entry["base64"]
                image_bytes = base64.b64decode(b64_data)
                logger.info("Successfully received base64 encoded image from artifacts.")
        # 2. Check for OpenAI compatible format: 'data' list containing 'b64_json' or 'url'
        elif "data" in resp_data and resp_data["data"]:
            image_entry = resp_data["data"][0]
            if "b64_json" in image_entry:
                b64_data = image_entry["b64_json"]
                image_bytes = base64.b64decode(b64_data)
                logger.info("Successfully received base64 encoded image from data.")
            elif "url" in image_entry:
                image_url = image_entry["url"]
                logger.info(f"Received image URL: {image_url}. Downloading image...")
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                image_bytes = img_response.content
                logger.info("Successfully downloaded image from URL.")
        
        if not image_bytes:
            raise Exception(f"Failed to extract image from response. JSON keys: {list(resp_data.keys())}")

        # Convert image bytes to a file-like object for pyTelegramBotAPI
        image_file = io.BytesIO(image_bytes)
        image_file.name = "generated_image.png"

        # Send the image back to the user
        try:
            bot.send_photo(
                chat_id=message.chat.id, 
                photo=image_file, 
                caption=f"✨ *Prompt:* {prompt}",
                reply_to_message_id=message.message_id,
                parse_mode="Markdown"
            )
        except Exception as reply_err:
            logger.debug(f"Failed to reply to user message, sending photo directly: {reply_err}")
            bot.send_photo(
                chat_id=message.chat.id, 
                photo=image_file, 
                caption=f"✨ *Prompt:* {prompt}",
                parse_mode="Markdown"
            )
        logger.info("Successfully sent generated photo back to user.")

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        try:
            bot.reply_to(
                message,
                f"❌ *Failed to generate image.*\n\n*Error Detail:*\n`{str(e)}`",
                parse_mode="Markdown"
            )
        except Exception:
            try:
                bot.send_message(
                    message.chat.id,
                    f"❌ *Failed to generate image.*\n\n*Error Detail:*\n`{str(e)}`",
                    parse_mode="Markdown"
                )
            except Exception as err_send_fail:
                logger.error(f"Failed to send error notification: {err_send_fail}")
    finally:
        # Clean up the status message
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        except Exception as delete_err:
            logger.debug(f"Failed to delete status message: {delete_err}")

@bot.message_handler(commands=["generate", "gen"])
def generate_image_command(message):
    """Handles /generate <prompt> or /gen <prompt> command in any chat (group or private)."""
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(
            message,
            "❌ *Please provide a prompt.*\n\n*Example:* `/generate a futuristic city`",
            parse_mode="Markdown"
        )
        return
    prompt = command_parts[1].strip()
    process_image_generation(message, prompt)

@bot.message_handler(func=lambda message: message.chat.type == "private")
def generate_image_private_handler(message):
    """Allows users to send plain text prompts directly in private DMs without the /generate command."""
    prompt = message.text.strip()
    if not prompt or prompt.startswith("/"):
        return
    process_image_generation(message, prompt)

@bot.message_handler(func=lambda message: message.chat.type != "private" and f"@{BOT_USERNAME}" in message.text)
def generate_image_mention_handler(message):
    """Handles messages in group chats that mention the bot directly."""
    bot_mention = f"@{BOT_USERNAME}"
    prompt = message.text.replace(bot_mention, "").strip()
    if not prompt:
        bot.reply_to(
            message,
            f"❌ *Please include a prompt.*\n\n*Example:* `@{BOT_USERNAME} a beautiful sunset`",
            parse_mode="Markdown"
        )
        return
    process_image_generation(message, prompt)

if __name__ == "__main__":
    logger.info("Starting Telegram Bot...")
    print(f"\n[INFO] NVIDIA Image Gen Bot is active!")
    print(f" - Model: {NVIDIA_MODEL}")
    print(f" - API URL: {NVIDIA_API_URL}")
    print(f" - Steps: {NVIDIA_STEPS}")
    print("Press Ctrl+C to stop.\n")
    
    # Keep the bot running and listening for updates
    bot.infinity_polling()

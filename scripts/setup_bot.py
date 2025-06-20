#!/usr/bin/env python3
"""
Setup Telegram bot with webhook and menu button for the Mini App
"""
import sys
import requests

# Bot configuration
BOT_TOKEN = "8165476295:AAFyLp4vqtHwFngH5MYDn5eOd2DdibHFGLo"
BOT_USERNAME = "talk2telegrambot"
WEBAPP_URL = "https://your-app-domain.com"  # Change this to your deployed URL

# For local testing, you can use ngrok or similar
# WEBAPP_URL = "https://abc123.ngrok.io"


def bot_request(method, **kwargs):
    """Make a request to Telegram Bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    response = requests.post(url, json=kwargs)
    result = response.json()

    if not result.get("ok"):
        print(f"Error: {result.get('description', 'Unknown error')}")
        return None

    return result.get("result")


def setup_bot():
    """Setup bot with commands and menu button"""

    # Set bot commands
    print("Setting bot commands...")
    commands = [
        {"command": "start", "description": "Start the bot and open the app"},
        {"command": "help", "description": "Get help on using the bot"},
        {"command": "app", "description": "Open the T2T2 app"},
    ]

    result = bot_request("setMyCommands", commands=commands)
    if result:
        print("✓ Commands set successfully")

    # Set menu button to open web app
    print("\nSetting menu button...")
    menu_button = {
        "type": "web_app",
        "text": "Open T2T2 App",
        "web_app": {"url": WEBAPP_URL},
    }

    result = bot_request("setChatMenuButton", menu_button=menu_button)
    if result:
        print("✓ Menu button set successfully")

    # Set bot description
    print("\nSetting bot description...")
    description = "T2T2 (Talk to Telegram 2) - Query your Telegram chat history with AI. This bot helps you search through your messages using natural language."

    result = bot_request("setMyDescription", description=description)
    if result:
        print("✓ Description set successfully")

    # Set bot short description
    print("\nSetting bot short description...")
    short_description = "Query your Telegram history with AI"

    result = bot_request("setMyShortDescription", short_description=short_description)
    if result:
        print("✓ Short description set successfully")

    print("\n✅ Bot setup complete!")
    print(f"\nYour bot is available at: https://t.me/{BOT_USERNAME}")
    print("\nNext steps:")
    print("1. Deploy your web app and update WEBAPP_URL in this script")
    print("2. Run this script again to update the menu button URL")
    print("3. Create a simple bot handler to respond to /start command")


def main():
    if len(sys.argv) > 1:
        global WEBAPP_URL
        WEBAPP_URL = sys.argv[1]
        print(f"Using webapp URL: {WEBAPP_URL}")
    else:
        print(f"Using default webapp URL: {WEBAPP_URL}")
        print(
            "Tip: Pass your webapp URL as an argument: python setup_bot.py https://your-app.com"
        )

    setup_bot()


if __name__ == "__main__":
    main()

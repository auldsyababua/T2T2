#!/usr/bin/env python3
"""
Quick script to update the bot's webapp URL
"""
import sys
import os

# Get the URL from command line
if len(sys.argv) != 2:
    print("Usage: python update_bot_url.py <webapp_url>")
    print("Example: python update_bot_url.py https://abc123.ngrok.io")
    sys.exit(1)

webapp_url = sys.argv[1]

# Update bot.py
bot_file = "bot.py"
with open(bot_file, 'r') as f:
    content = f.read()

# Replace the WEBAPP_URL line
import re
content = re.sub(
    r'WEBAPP_URL = os\.getenv\("WEBAPP_URL", "[^"]+"\)',
    f'WEBAPP_URL = os.getenv("WEBAPP_URL", "{webapp_url}")',
    content
)

with open(bot_file, 'w') as f:
    f.write(content)

print(f"✅ Updated bot.py with webapp URL: {webapp_url}")

# Also run the setup script to update the menu button
os.system(f"python scripts/setup_bot.py {webapp_url}")

print("\n✅ Bot configuration updated!")
print("Now restart the bot (Ctrl+C and run 'python bot.py' again)")
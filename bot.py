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
    try:
        if str(message.chat.id) == getenv("TELEGRAM_USER_ID"):
            topics_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for topic in list(topics.find()):
                topics_kb.add(types.KeyboardButton(topic["name"]))

            bot.send_message(message.chat.id, "Твоя роль: *користувач*", parse_mode="Markdown", reply_markup=topics_kb)

        elif str(message.chat.id) == getenv("TELEGRAM_HELPER_ID"):
            bot.send_message(message.chat.id, "Твоя роль: *помічник*", parse_mode="Markdown")

    except Exception as ex:
        print(ex)
        bot.send_message(message.chat.id, "упс(")


@bot.message_handler(content_types=["text"])
def text_message(message):
    try:
        if str(message.chat.id) == getenv("TELEGRAM_USER_ID"):
            topic = topics.find_one({"name": message.text})

            if topic:
                tickets_kb = types.InlineKeyboardMarkup()
                for ticket in list(tickets.find({"topic_number": topic["number"]})):
                    tickets_kb.add(types.InlineKeyboardButton(f"#{ticket['number']} {ticket['question']}", callback_data=f"ticket-{ticket['number']}"))

                bot.send_message(message.chat.id, f"Тема: *{topic['name']}*", parse_mode="Markdown", reply_markup=tickets_kb)

            else:
                bot.send_message(message.chat.id, "Тему не знайдено", parse_mode="Markdown")

    except Exception as ex:
        print(ex)
        bot.send_message(message.chat.id, "упс(")


@bot.callback_query_handler(func=lambda call: call.data.startswith("ticket"))
def ticket_message(call):
    try:
        if str(call.message.chat.id) == getenv("TELEGRAM_USER_ID"):
            ticket_number = int(call.data.split("-")[1])
            ticket = tickets.find_one({"number": ticket_number})
            topic = topics.find_one({"number": ticket["topic_number"]})
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Тема: *{topic['name']}*\nНомер білету: *{ticket['number']}*\nПитання: *{ticket['question']}*\n\n{ticket['answer']}", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Надіслати помічнику", callback_data=f"help-{ticket['number']}")), parse_mode="Markdown")

    except Exception as ex:
        print(ex)
        bot.answer_callback_query(callback_query_id=call.id, text="упс(")


@bot.callback_query_handler(func=lambda call: call.data.startswith("help"))
def help_message(call):
    try:
        if str(call.message.chat.id) == getenv("TELEGRAM_USER_ID"):
            ticket_number = int(call.data.split("-")[1])
            ticket = tickets.find_one({"number": ticket_number})
            topic = topics.find_one({"number": ticket["topic_number"]})
            bot.send_message(getenv("TELEGRAM_HELPER_ID"), f"Тема: *{topic['name']}*\nНомер білету: *{ticket['number']}*\nПитання: *{ticket['question']}*\n\n{ticket['answer']}", parse_mode="Markdown")
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=f"Тема: *{topic['name']}*\nНомер білету: *{ticket['number']}*\nПитання: *{ticket['question']}*\n\n{ticket['answer']}",
                                  parse_mode="Markdown")
            bot.answer_callback_query(callback_query_id=call.id, text="Білет надіслано")

    except Exception as ex:
        print(ex)
        bot.answer_callback_query(callback_query_id=call.id, text="упс(")


if __name__ == "__main__":
    bot.send_message(getenv("TELEGRAM_ADMIN_ID"),"Бот запущений")
    bot.infinity_polling()

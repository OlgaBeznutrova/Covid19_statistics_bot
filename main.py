import os

import telebot
import flag

from flask import Flask, request
from jinja2 import Template
from telebot import types

from common.containers import Container
from common.countries_alpha2_codes import alpha2_codes

# bot initialization
token = os.getenv("API_BOT_TOKEN")
bot = telebot.TeleBot(token)

mongo_context = Container.mongo_db_context()
country_service = Container.country_service()
stats_service = Container.statistics_service()

commands = {
    "start": "Start using this bot",
    "help": "Useful information about this bot",
    "statistics": "Statistics by user`s queries",
    "contacts": "Developer contacts"
}


# start command handler
@bot.message_handler(commands=["start"])
def start_command_handler(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_geo = types.KeyboardButton(text="send location", request_location=True)
    markup.add(button_geo)

    bot.send_message(chat_id=chat_id,
                     text=f"Hello, {message.from_user.first_name}! Write country name or send me the location:",
                     reply_markup=markup)

    # help_command_handler(message)


# help command handler
@bot.message_handler(commands=["help"])
def help_command_handler(message):
    chat_id = message.chat.id
    help_text = "The following commands are available\n"
    for command, description in commands.items():
        help_text += f"/{command}: {description}\n"
    bot.send_message(chat_id, help_text)


# contacts command handler
@bot.message_handler(commands=["contacts"])
def contacts_command_handler(message):
    chat_id = message.chat.id
    with open("templates/contacts.html", encoding="UTF-8") as file:
        template = Template(file.read())
        bot.send_message(
            chat_id=chat_id,
            text=template.render(username=message.chat.username),
            parse_mode="HTML"
        )


# hi message handler
@bot.message_handler(func=lambda message: message.text.lower() in ["hi", "hello"])
def hi_message_handler(message):
    chat_id = message.chat.id
    with open(file="templates/hi.html", encoding="UTF-8") as file:
        template = Template(file.read())
    bot.send_message(
        chat_id=chat_id,
        text=template.render(user_name=message.from_user.first_name, greeting=message.text.title()),
        parse_mode="HTML"
    )


# geo command handler
@bot.message_handler(content_types=["location"])
def geo_command_handler(message):
    chat_id = message.chat.id
    geo_result = country_service.get_country_information_by_lat_lng(message.location.latitude,
                                                                    message.location.longitude)
    covid_statistics = stats_service.get_statistics_by_country_name(geo_result["countryName"], message.chat.username)
    bot.send_message(chat_id, covid_statistics, parse_mode="HTML")


# query statistics command handler
@bot.message_handler(commands=["statistics"])
def statistics_command_handler(message):
    chat_id = message.chat.id
    statistics = stats_service.get_statistics_of_users_queries()
    bot.send_message(chat_id=chat_id, text=statistics, parse_mode="HTML")


# hidden statistics command handler
@bot.message_handler(func=lambda message: len(message.text.split()) == 3)
def hidden_stats_command_handler(message):
    pass_char, days, stats_key = message.text.split()
    if pass_char == os.getenv("PASS_CHAR") and stats_key == os.getenv("STATS_KEY"):
        chat_id = message.chat.id
        hidden_stats = stats_service.get_hidden_stats(int(days))
        bot.send_message(chat_id=chat_id, text=hidden_stats)
    else:
        country_statistics_command_handler(message)


# country statistics command handler
@bot.message_handler(func=lambda message: True, content_types=["text"])
def country_statistics_command_handler(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id=chat_id, action="typing")
    username = message.chat.username
    country_name = message.text.strip()

    possible_countries = country_service.get_countries_by_part_of_name(country_name)

    if not possible_countries["results"]:
        mongo_context.save_country_query(country_name, username, is_known=False)
        with open("templates/no_country.html", encoding="UTF-8") as file:
            template = Template(file.read())
        bot.send_message(
            chat_id=chat_id,
            text=template.render(text_command=country_name),
            parse_mode="HTML"
        )

    elif possible_countries["results"] == 1:
        country = possible_countries["response"][0]
        try:
            statistics = stats_service.get_statistics_by_country_name(country, username)
            bot.send_message(
                chat_id=chat_id,
                text=f"{flag.flag(alpha2_codes[country])} {statistics}",
                parse_mode="HTML")
        except Exception as e:
            raise e

    elif possible_countries["results"] > 1:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for country in possible_countries["response"]:
            markup.add(types.InlineKeyboardButton(
                text=f"{flag.flag(alpha2_codes[country])} {country}",
                callback_data=country))
        bot.send_message(
            chat_id=chat_id,
            text="Which country were you looking for:",
            reply_markup=markup
        )


# callback country command handler
@bot.callback_query_handler(func=lambda call: True)
def callback_country_statistics_command_handler(call):
    call.message.text = call.data
    bot.answer_callback_query(callback_query_id=call.id)
    country_statistics_command_handler(call.message)


# set webhook
server = Flask(__name__)


@server.route("/" + token, methods=["POST"])
def get_message():
    json_string = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("HEROKU_URL") + token)
    return "!!", 200


# application entry point
if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# if __name__ == '__main__':
#    bot.remove_webhook()
#    bot.infinity_polling()

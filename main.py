import telebot
import requests
import sqlite3
from telebot import types



bot = telebot.TeleBot(token="7123609372:AAE72dqH4AzAAkN7Wp2wngD2u7rb7MYFoV8")

weather_api = "90928287d38d2f3276345c816f823133"

name = None

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, username TEXT, password TEXT, credits INTEGER )")
    conn.commit()
    cur.close()
    conn.close()

    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton(text="Yes"))
    markup.add(types.KeyboardButton(text="No, I want to register"))

    bot.send_message(message.chat.id, "Hello! I'm glad to see you \n\nHave you used our platform before?", reply_markup=markup)
    bot.register_next_step_handler(message, auth)


def auth(message):
    markup = types.ReplyKeyboardRemove()
    if message.text == "Yes":
        bot.send_message(message.chat.id, "Enter your name", reply_markup=markup)
        bot.register_next_step_handler(message, auth_log)

    elif message.text == "No, I want to register":
        username = message.from_user.username
        conn = sqlite3.connect('users.sql')
        cur = conn.cursor()
        cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = ?)", (username,))
        exists = cur.fetchone()
        cur.close()
        conn.close()
        if exists[0] == 1:
            markup = types.ReplyKeyboardMarkup()
            markup.add(types.KeyboardButton(text="Yes"))
            bot.send_message(message.chat.id, "You've already registered before, try to login")
            bot.send_message(message.chat.id, "Do u have an account?", reply_markup=markup)
            bot.register_next_step_handler(message, auth)
        else:
            bot.send_message(message.chat.id, "Ok, Let's create an account! \n\nEnter your name", reply_markup=markup)
            bot.register_next_step_handler(message, auth_reg)

def auth_log(message):
    global name
    name = message.text
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE name = ?)", (name,))
    if cur.fetchone()[0] == 1:
        bot.send_message(message.chat.id, "Enter your password")
        bot.register_next_step_handler(message, auth_log_2)
        name = message.text
    else:
        bot.send_message(message.chat.id, "There's no such person. The name must be written wrong.")
        bot.send_message(message.chat.id, "Try again!")
        bot.register_next_step_handler(message, auth_log)


def auth_log_2(message):
    global name
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()

    cur.execute(f"SELECT password FROM users WHERE name=?", (name,))
    password = cur.fetchone()

    if message.text == password[0]:
        bot.send_message(message.chat.id, "Welcome " + name + "!")
        bot.send_message(message.chat.id, "Enter the city name to check the weather")

    elif message.text != password[0]:
        bot.send_message(message.chat.id, "Wrong password!")
        bot.send_message(message.chat.id, "Try again!")
        bot.register_next_step_handler(message, auth_log_2)


def auth_reg(message):
    global name
    name = message.text
    bot.send_message(message.chat.id, "Enter your password")
    bot.register_next_step_handler(message, auth_reg_2)


def auth_reg_2(message):
    global name
    password = message.text
    username = message.from_user.username
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, password, username) VALUES (?, ?, ?)", (name, password, username))
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Welcome " + name + "!")
    bot.send_message(message.chat.id, "Enter the city name to check the weather")


@bot.message_handler(content_types=['text'])
def get_weather(message):
    city = message.text.strip()
    res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api}&units=metric")
    response = res.json()

    if response.get("cod") == 200:
        temp = response["main"]["temp"]
        bot.send_message(message.chat.id, f"The temperature in {city} is {int(temp)} degrees Celsius.")
        bot.send_message(message.chat.id, "Any other cities to check?")
    else:
        bot.send_message(message.chat.id, "City not found or there was an error retrieving the weather data.")


bot.polling(non_stop=True)
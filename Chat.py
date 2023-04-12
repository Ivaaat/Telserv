from subprocess import check_output
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from config import TOKEN, user_id, users_command
import os

bot = telebot.TeleBot(TOKEN)

 
def delete_mess(message):
    for i in range(20):
        bot.delete_message(message.chat.id, message.message_id - i)


@bot.message_handler(content_types = ["text"])
def start (message) :
    try:
        delete_mess(message)
    finally:
        if user_id == message.chat.id: #проверяем, что пишет именно владелец
            text = f'''Добро пожаловать {message.from_user.first_name}\n
            /vpn - Создать/Удалить клиент OpenVPN\n
            /users - Список пользователей\n
            /cmd - Выполнение команд'''
            msg = bot.send_message(message.chat.id, text)
            bot.register_next_step_handler(msg, contin)

def contin(message):
    try:
        delete_mess(message)
    finally:
        match message.text:
            case '/vpn':
                create_vpn(message)
            case '/users':
                get_users(message)
            case '/cmd':
                set_cmd(message)
            case _:
                start(message)


#Создание кнопок под сообщением
def create_vpn(message):
    bot.send_message(message.from_user.id, "Создать/Удалить клиент OpenVPN?", reply_markup=keyboard_create())


def get_users(message):
    messg = check_output(users_command, shell = True).decode('UTF-8')
    bot.send_message(message.from_user.id, f"Клиенты OpenVPN:\n{messg}")
    start(message)


def set_cmd(message):
    msg = bot.send_message(message.chat.id, "Введи команду на сервер")
    bot.register_next_step_handler(msg, cmd)
    

def cmd(message):
    try:
        bot.send_message(message.chat.id, check_output(message.text, shell = True))
    except:
        bot.send_message(message.chat.id, "Invalid input") 
    start(message)


def keyboard_create ():
    return InlineKeyboardMarkup(
              keyboard=[
                    [InlineKeyboardButton(text="Создать", callback_data="Create"), 
                    InlineKeyboardButton(text="Удалить", callback_data="Del"),
                    InlineKeyboardButton(text="Выход", callback_data="exit")]
              ]
    )


@bot.callback_query_handler(func=lambda call: call.data == "exit")
def callback_function(call):
    msg = bot.send_message(call.from_user.id, "Выход")
    bot.clear_step_handler_by_chat_id(chat_id=call.from_user.id)
    start (msg)
    bot.answer_callback_query(callback_query_id = call.id)
     

#Функция кнопок создать/удалить
@bot.callback_query_handler(func=lambda call: call.data in ["Create", "Del"])
def callback_function3(calb):
    bot.clear_step_handler_by_chat_id(chat_id=calb.from_user.id)
    if calb.data == "Create":
        messg = "Введи имя клиента\n"
        go = talk
    elif calb.data == "Del":
        users = users_command
        messg = "Введи номер клиента\n" + check_output(users, shell = True).decode('UTF-8')
        go = deltalk
    msg = bot.send_message(calb.from_user.id, messg + "Или нажмите Выход!", reply_markup=markup_exit())
    bot.register_next_step_handler(msg, go, messg)
    bot.answer_callback_query(callback_query_id = calb.id)


def markup_exit():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Выход", callback_data="exit"))
    return markup


#Создание конфиги на сервере
def talk(message, text_message):
    text = message.text
    chat_id = message.chat.id
    try:
        if text.isalpha() and len(text) < 6:
            path_to_create = f'sudo ./script.sh 1 {text}'
            res = check_output(path_to_create, shell = True).decode('UTF-8')
            if res.endswith("another name.\n"):
                raise KeyError
            name_doc = os.getcwd().split('/')[2]
            doc = open(f'/home/{name_doc}/{text}.ovpn','rb')
            bot.send_document(chat_id, doc)
            return start(message)
        else:
            raise KeyError
    except KeyError:
        msg = bot.send_message(chat_id, "Введи новое имя без цифр и символов", reply_markup=markup_exit())
        return bot.register_next_step_handler(msg, talk, text_message)


#Удаление конфиги на сервере   
def deltalk(message, text_message):
    text = message.text
    chat_id = message.chat.id
    count = len(text_message.split('\n')) - 2
    if text.isdigit() and count >= int(text):
        delClient = f'sudo ./script.sh 2 {text}'
        check_output(delClient, shell = True)
        bot.send_message(chat_id, f"Клиент {text} удалён")
        return start(message)
    msg = bot.send_message(chat_id, text_message, reply_markup=markup_exit())
    bot.register_next_step_handler(msg, deltalk, text_message)


if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling()
        except:
            time.sleep(10)

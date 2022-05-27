from subprocess import check_output
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove
import time
from telebot.handler_backends import State, StatesGroup
from config import TOKEN, msg_nahui, user_id, send_messages
from pymongo import MongoClient
import datetime


bot = telebot.TeleBot(TOKEN)

client = MongoClient()
db = client.Telserv #База данных
vpn= db.vpn1 #Коллекция

@bot.message_handler(commands=['start'])
def start (message) :
    if (user_id == message.chat.id): #проверяем, что пишет именно владелец
        msg = "Добро пожаловать " + message.from_user.first_name +  " \n\nЧто здесь можно сделать:\n\n /vpn - Создать/Удалить клиент OpenVPN\n\n /user - Список пользователей\n\n Команды к серверу - Выполнение команд"
        bot.set_my_commands(commands=[BotCommand("vpn", "Create VPN"), BotCommand("user", "List of users")])
        bot.delete_message(message.from_user.id, message.message_id-1)
        bot.send_message(message.from_user.id,msg)
    else :
        bot.send_message(message.chat.id, msg_nahui)


@bot.message_handler(regexp="del")
def delmes (message) :
     bot.delete_message(message.chat.id,message.message_id-1)

#mongodb
def MongoTelservDB (numb, messg, id_name):
    name_vpn = {"Number": str(numb),
                "Name": messg,
                "Create": id_name}
    vpn_id = vpn.insert_one(name_vpn).inserted_id

#Удаление клавиатуры
@bot.message_handler(regexp="done")
def users(message):
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.from_user.id, "Remove Keyboard", reply_markup=markup)


#@bot.message_handler(regexp="user")
def users1(message):
    userslist = 'Список пользователей:\n\nКлиенты   Имя   Создатель\n'
    for x in vpn.find():
        number = x['Number']
        name = x['Name']
        create = x["Create"]
        #date = x["date"]
        userslist +='     '  + str(number)+ '              ' +  str(name) + '       ' + str(create)+'\n'
    bot.send_message(message.chat.id, userslist)

bot.register_message_handler(users1, commands=['user'])

def users():
    userslist = 'Нужно выбрать номер клиента:\n'
    for x in vpn.find():
        number = x['Number']
        name = x['Name']
        create = x["Create"]
        #date = x["date"]
        userslist += str(number)+ ' ' +  str(name) + ' ' + str(create)+'\n'
    return userslist


#Создание кнопок под сообщением
@bot.message_handler(commands=["vpn"])
def get_keyboard(message):
   
     bot.delete_my_commands(scope=None, language_code=None)
     bot.send_message(message.from_user.id, "Создать/Удалить клиент OpenVPN?",  reply_markup=keyboard_create())


def keyboard_create ():
    return InlineKeyboardMarkup(
              keyboard=[
                       [InlineKeyboardButton(text="Создать", callback_data="Create"), 
                        InlineKeyboardButton(text="Удалить", callback_data="Del")]
              ]
    )


#Функция кнопок создать/удалить
@bot.callback_query_handler(func=lambda call: call.data == "Create" or "Del")
def callback_function3(calb):
     #path_to_del = "sudo cat /etc/openvpn/easy-rsa/pki/index.txt | grep \"^V\" | cut -d \'=\' -f 2 |sed \'1d\'| sed \'s/^/1)/;n;s/^/2)/;n;s/^/3)/;n;s/^/4)/\' | sed \'1i\Какой удалить клиент :\'"
     #commd = check_output(path_to_del, shell = True,universal_newlines=True)
     if calb.data=="Create":
               messg = send_messages[:20]
               go = talk
     elif calb.data=="Del":
               messg = users()
               go = deltalk
     msg = bot.send_message(calb.from_user.id, messg + "\nИли нажмите Выход!", reply_markup = keyb_markup ())
     bot.delete_message(calb.from_user.id, calb.message.message_id)
     bot.set_my_commands(commands=[BotCommand("vpn", "Create VPN"), BotCommand("user", "List of users")])
     bot.register_next_step_handler(msg, go)
     bot.answer_callback_query(callback_query_id = calb.id)


def keyb_markup ():
    #return types.ReplyKeyboardMarkup(markup = [[types.KeyboardButton("Выход")]])
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = KeyboardButton("Выход")
        markup.add(btn1)
        return markup        


#Создание конфиги на сервере
def talk(message):
      text = message.text
      chat_id = message.chat.id
      if (text == 'Выход'): 
             exit_func (message)
      elif not check_en(text) :
             msg=bot.send_message(chat_id, send_messages)
             bot.register_next_step_handler(msg, talk)
             return
      else :
             path_to_create = "sed '3c\export CLIENT="+'"'+text+'"'+"' ./script.sh >./scr.sh | sudo ./scr.sh"
             res = check_output(path_to_create, shell = True, universal_newlines = True)
             res = "another name." in  res
             if res :
                   send_messages1 = send_messages.replace (' ', ' новое ', 1)
                   msg = bot.send_message(chat_id, send_messages1[:28])
                   bot.register_next_step_handler(msg, talk)
                   return
             doc= open('./'+text+'.ovpn','rb')
             Number = vpn.count_documents({})+1
             MongoTelservDB (Number, text, message.from_user.first_name)
             bot.set_my_commands(
                                 commands=[
                                          BotCommand("vpn", "Create VPN"),
                                          BotCommand("user", "List of users")
                                 ],
             )
             bot.send_document(chat_id, doc, reply_markup = ReplyKeyboardRemove())
	
def exit_func (message):
    i = 0
    while i <= 1:
        bot.delete_message(message.chat.id, message.message_id-i)
        i += 1
    return bot.send_message(message.chat.id, "Заходи если че", reply_markup = telebot.types.ReplyKeyboardRemove())             


#Удаление конфиги на сервере   
def deltalk(message):
      text = message.text
      chat_id = message.chat.id
      if (text == 'Выход'):
           exit_func (message)
      else :
          if not text.isdigit():
            msg = bot.send_message(chat_id, "Введи номер клиента")
            bot.register_next_step_handler(msg, deltalk)
            return
          result = vpn.delete_one ({"Number" :str(text)})
          delClient = "sed -e '4d; y/1/2/; 3c\export CLIENTNUMBER=" + '"' + text + '"' + "'  script.sh >./scr.sh | sudo ./scr.sh"
          check_output(delClient, shell = True)
          bot.delete_message(chat_id, message.message_id-1)
          bot.send_message(chat_id, "Клиент " + text + " удалён", reply_markup = ReplyKeyboardRemove())


#Функция проверки ввода только латиницы
def check_en (check_test):
      if  len(check_test)>6 :
          return False
      char_en = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
      i = 0
      while i <= len(check_test)-1:
          j = 0
          while j <= len(char_en)-1:
              if check_test [i] == char_en[j]:
                 break
              j+=1
              if j == (len(char_en)-1) :
                 return False
          i+=1
      return True


#Произвольная команда на сервер
@bot.message_handler(content_types = ["text"])
def main(message):
   if (user_id == message.chat.id): #проверяем, что пишет именно владелец
      comand = message.text  #текст сообщения
      try: #если команда невыполняемая - check_output выдаст exception
         bot.send_message(message.chat.id, check_output(comand, shell = True))
      except:
         bot.send_message(message.chat.id, "Invalid input") #если команда некорректна
   else :
        bot.send_message(message.chat.id, msg_nahui)
if __name__ == '__main__':
    while True:
        try:#добавляем try для бесперебойной работы
            bot.polling(none_stop = True)#запуск бота
        except:
            time.sleep(10)#в случае падения




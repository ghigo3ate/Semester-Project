import os
import telebot
import datetime
from threading import Thread
import time

BOT_TOKEN = os.environ.get('BOT_TOKEN')
file_path = 'reminders.csv'

bot = telebot.TeleBot(BOT_TOKEN)

date_format = '%d.%m.%Y %H:%M'

# Start command
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I'm a reminder bot. Type /help to see commands.")

# Help command
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Available commands:\n/remind - create a reminder\n/list - view the list of reminders\n/set - set the status of the reminder\n/week - view the list of reminders for a week\n/help - view the list of commands")

# Create reminder
@bot.message_handler(commands=['remind'])
def setReminderTextMessage(message):
    text = "Enter text for reminder:"
    send_message = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(send_message, setReminderText)

def setReminderText(message):
    if(message.text[0] == '/'):
        bot.send_message(message.chat.id, "Creation canceled")
        return
    reminder_object = {}
    reminder_object["text"] = message.text
    setReminderDateMessage(message, reminder_object)

def setReminderDateMessage(message, reminder_object):
    send_message = bot.send_message(message.chat.id, f"Enter the reminder date and time in `dd.mm.yyyy hh:mm` format")
    bot.register_next_step_handler(send_message, setReminderDate, reminder_object)

def setReminderDate(message, reminder_object):
    if(message.text[0] == '/'):
        bot.send_message(message.chat.id, "Creation canceled")
        return

    try:
        reminder_date = datetime.datetime.strptime(message.text, date_format)
        if(reminder_date < datetime.datetime.now()):
            bot.send_message(message.chat.id, "Please enter a valid date")
            setReminderDateMessage(message)
            return

        reminder_object["date"] = message.text
        createReminder(message, reminder_object)
    # If the date validation goes wrong
    except ValueError:
        bot.send_message(message.chat.id, "Invalid date format, should be `dd.mm.yyyy hh:mm`")
        setReminderDate(message)
        return

def createReminder(message, reminder_object):
    reminder_object["status"] = False

    file = open(file_path, 'a')
    file.write(f"{reminder_object['text']}&{reminder_object['date']}&{reminder_object['status']}&{message.chat.id}\n")
    file.close()

    bot.send_message(message.chat.id, f"Reminder created! You can view the list of reminders using the /list command")

# Get reminders
@bot.message_handler(commands=['list'])
def getReminders(message):
    file = open(file_path, 'r')
    reminders = file.read()
    file.close()

    json_array = []
    id = 0
    for line in reminders.splitlines():
        data = []
        data = line.split('&')

        json_data = {
            'text': data[0],
            'date': data[1],
            'status': data[2],
            'id': id,
            'chat_id': data[3]
        }
        json_array.append(json_data)
        id += 1

    bot.send_message(message.chat.id, f"List of reminders:")

    for reminder in json_array:
        if reminder['chat_id'] != str(message.chat.id):
            continue
        status_text = "Done" if reminder['status'] == "True" else "Not done"
        bot.send_message(message.chat.id, f"Text: {reminder['text']}\nDate: {reminder['date']}\nStatus: {status_text}\nId: {reminder['id']}\n")


# Set status of reminder
@bot.message_handler(commands=['set'])
def setStatusMessage(message):
    send_message = bot.send_message(message.chat.id, f"Enter reminder id")
    bot.register_next_step_handler(send_message, setStatusHandler)

def setStatus(id):
    file = open(file_path, 'r')
    reminders = file.read()
    file.close()

    json_array = []
    for line in reminders.splitlines():
        data = []
        data = line.split('&')

        json_data = {
            'text': data[0],
            'date': data[1],
            'status': data[2],
            'chat_id': data[3]
        }

        json_array.append(json_data)

    json_array[id]['status'] = "True"

    file = open(file_path, 'w')
    for reminder in json_array:
        file.write(f"{reminder['text']}&{reminder['date']}&{reminder['status']}&{reminder['chat_id']}\n")
    file.close()

def setStatusHandler(message):
    try:
        id = int(message.text)
        setStatus(id)
        bot.send_message(message.chat.id, f"Reminder with id {id} is marked as completed")
    except ValueError:
        bot.send_message(message.chat.id, f"Incorrect id format")
        return
    

# Get reminders for week
@bot.message_handler(commands=['week'])
def getRemindersForWeek(message):
    file = open(file_path, 'r')
    reminders = file.read()
    file.close()

    json_array = []
    key = 0
    for line in reminders.splitlines():
        data = []
        data = line.split('&')

        json_data = {
            'text': data[0],
            'date': data[1],
            'status': data[2],
            'id': key,
            'chat_id': data[3]
        }
        key += 1
        json_array.append(json_data)

    bot.send_message(message.chat.id, f"List of reminders for the week:")

    for reminder in json_array:
        if(reminder['status'] == "False"):
            reminder_date = datetime.datetime.strptime(reminder['date'], date_format)
            if(reminder_date < datetime.datetime.now() + datetime.timedelta(days=7)):
                if reminder['chat_id'] != str(message.chat.id):
                    continue

                status_text = "Done" if reminder['status'] == "True" else "Not done"
                bot.send_message(message.chat.id, f"Text: {reminder['text']}\nДата: {reminder['date']}\Status: {status_text}\nId: {reminder['id']}\n")

# Notification async

def notification():
    print("Notification started")
    file = open(file_path, 'r')
    reminders = file.read()
    file.close()

    json_array = []
    key = 0
    for line in reminders.splitlines():
        data = []
        data = line.split('&')

        json_data = {
            'text': data[0],
            'date': data[1],
            'status': data[2],
            'chat_id': data[3],
            'id': key
        }
        key += 1
        json_array.append(json_data)

    for reminder in json_array:
        if(reminder['status'] == "False"):
            reminder_date = datetime.datetime.strptime(reminder['date'], date_format)
            if(reminder_date < datetime.datetime.now()):
                bot.send_message(reminder['chat_id'], f"Reminder: {reminder['text']}")
                setStatus(reminder['id'])

def loop():
    while True:
        time.sleep(3)
        notification()


# Run bot
if __name__ == "__main__":
    thread = Thread(target=loop, daemon=True)
    thread.start()
    bot.infinity_polling()



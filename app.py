from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.url_message import URLMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

import time
import logging
import sched
import threading

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
  name='PythonSampleBot',
  avatar='http://viber.com/avatar.jpg',
  auth_token='4dfe33affba7da65-2a52124984649896-1b3e27db8dd93f2e'
))

CITIES = (
    ('minsk', 'Минск'),
    ('brest', 'Брест'),
    ('vitebsk', 'Витебск'),
    ('gomel', 'Гомель'),
    ('grodno', 'Гродно'),
    ('mogilev', 'Могилёв'),
)

PROFILES = (
    ('employee', 'Я сотрудник компании'),
    ('applicant', 'Я хочу у вас работать'),
)

EMPLOYEE_QUEST = (
    ('1','Вопрос по оплате труда'),
    ('2','Как оплачивается топливо, если использую свой автомобиль в работе?'),
    ('3','Как оплачивается мобильная связь?'),
    ('4','Вопрос по дополнительным выплатам'),
)

def get_buttons(action_type, items):
    return [{
        "Columns": 3,
        "Rows": 1,
        "BgColor": "#32b67a",
        # "BgMedia": "http://link.to.button.image",
        # "BgMediaType": "picture",
        "BgLoop": True,
        "ActionType": 'reply',
        "ActionBody": item[0],
        "ReplyType": "message",
        "Text": item[1]
    } for item in items]

@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))

    viber_request = viber.parse_request(request.get_data().decode('utf8'))

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message
        text = message.text
        text = text.split('|')
        text_type = text[0]
        text_message = ''

        keyboard = {
            "DefaultHeight": True,
            "BgColor": "#1a191d",
            "Type": "keyboard",
            "Buttons": []
        }

        reset_button = [{
            "Columns": 6,
            "Rows": 1,
            "BgColor": "#3fa7f3",
            "BgLoop": True,
            "ActionType": "reply",
            "ActionBody": "select_profile",
            "ReplyType": "message",
            "Text": "Сбросить прогресс"
        }]

        buttons = {}

        if text_type == 'select_profile':
            text_message = "Кто вы?"
            items = [item[1] for item in PROFILES]
            buttons = get_buttons('select_question', PROFILES)

        elif text_type == 'applicant':
            text_message = "В каком регионе Вы проживаете?"
            items = [item[1] for item in CITIES]
            buttons = get_buttons('select_city', CITIES)

        elif text_type == 'employee':
            text_message = "Какой вопрос Вас интересует?"
            items = [item[1] for item in EMPLOYEE_QUEST]
            buttons = get_buttons('employee_form', EMPLOYEE_QUEST)

        else:
            text_message = "Что-то не так. Нажмите 'Сбросить прогресс'"

        messages = []

        keyboard_buttons = keyboard.get('Buttons', [])
        keyboard_buttons.extend(buttons)
        keyboard_buttons.extend(reset_button)
        
        keyboard['Buttons'] = keyboard_buttons

        messages.append(TextMessage(text=text_message, keyboard=keyboard))

        viber.send_messages(viber_request.sender.id, messages)


    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="Спасибо за активацию бота!")
        ])

    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    elif isinstance(viber_request, ViberConversationStartedRequest):
        keyboard = {
            "DefaultHeight": True,
            "BgColor": "#1a191d",
            "Type": "keyboard",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "BgColor": "#3fa7f3",
                    "BgLoop": True,
                    "ActionType": "reply",
                    "ActionBody": "select_profile",
                    "ReplyType": "message",
                    "Text": "Активировать Бот 'Работа'"
                }
            ]
        }
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="Добрый день. Для продолжения, нажмите на кнопку", keyboard=keyboard)
        ])

    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

def set_webhook(viber):
    viber.set_webhook('https://flask-app-9bgq9.ondigitalocean.app/')

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    context = ('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=8080, debug=True, ssl_context=context)
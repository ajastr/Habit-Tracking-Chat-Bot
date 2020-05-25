import os
import sys
import os.path
from os import path
import ssl
from flask import Flask, request
from fbmessenger import BaseMessenger
from fbmessenger.templates import GenericTemplate
from fbmessenger.elements import Text, Button, Element
from flask_apscheduler import APScheduler

from datetime import date
from janusz import Janusz
from database_helper import DatabaseHelper

#FB TOKENS
os.environ['FB_PAGE_TOKEN'] = ''
os.environ['FB_VERIFY_TOKEN'] = ''

def process_message(message):
    app.logger.debug('Message received: {}'.format(message))

    if 'attachments' in message['message']:
        if message['message']['attachments'][0]['type'] == 'location':
            app.logger.debug('Location received')
            response = Text(text='{}: lat: {}, long: {}'.format(
                message['message']['attachments'][0]['title'],
                message['message']['attachments'][0]['payload']['coordinates']['lat'],
                message['message']['attachments'][0]['payload']['coordinates']['long']
            ))
            return response.to_dict()

    #Response if none of the states are activated
    if 'text' in message['message']:
        msg = message['message']['text'].lower()
        response = Text(text='Sorry didn\'t understand that: {}'.format(msg))

        if 'yay' == msg:
            response = Text(text='YAY!')
        if 'hehe' in msg:
            response = Text(text='HueHueHue')
        if 'pys' == msg:
            response = Text(text='ptys')
        return response.to_dict()

class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        action = process_message(message)
        res = self.send(action, 'RESPONSE')
        app.logger.debug('Response: {}'.format(res))

    def get_sender_id(self,payload):
        for entry in payload['entry']:
            for message in entry['messaging']:
                if message.get("is_echo") is True:
                    break
                return message['sender']['id']

    def get_message(self,payload):
        for entry in payload['entry']:
            for message in entry['messaging']:
                if message['sender']['id'] == "2423755924562754": #ID of the chatbot- Eleminate echo
                    return ""
                if message.get('message'):
                    if 'text' in message['message']:
                        msg = message['message']['text'].lower()
                        return msg
                    if "attachments" in message['message']:
                        att = message['message']['attachments'][0]
                        if "payload" in att:
                            pld = att['payload']
                            if "sticker_id" in pld:
                                sticker_id= pld["sticker_id"]
                                if sticker_id == 369239263222822: #thubms up sticker
                                    return "yes"
                                return sticker_id
                            return pld
        return ""

    def janusz_send(self,text,id):
        messenger.client.send({'text': text }, id,'RESPONSE', notification_type='REGULAR',timeout=None, tag=None)

    def janusz_send_list(self,lst,id):
        for i in range(len(lst)):
            messenger.client.send({'text':lst[i]}, id,'RESPONSE', notification_type='REGULAR',timeout=None, tag=None)

    def janusz_send_url(self,url,id):
        messenger.client.send({"attachment":{"type":"image","payload":{"url":url}}}, id,'RESPONSE', notification_type='REGULAR',tag=None)

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

app.debug = True
messenger = Messenger(os.environ.get('FB_PAGE_TOKEN'))

DH = DatabaseHelper()
janusze = {}

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        print(os.environ.get('FB_VERIFY_TOKEN'))
        print('')
        print(request.args.get('hub.verify_token'))
        print('')
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            if request.args.get('init') and request.args.get('init') == 'true':
                return ''
            return request.args.get('hub.challenge')
        raise ValueError('FB_VERIFY_TOKEN does not match.')
    elif request.method == 'POST':

        sender =  messenger.get_sender_id(request.get_json(force=True))
        pld = request.get_json(force=True)
        msg = messenger.get_message(request.get_json(force=True))

        #Create an instance for each user and save in dictionary
        if sender not in janusze:
            janusze[sender] = Janusz(DH,sender)
        jan = janusze[sender]
        print(janusze)
        print("Message from sender", sender, "is:", msg)
        print('')
        jan.check_timeout()

        if jan.state == "ask_for_next_day":
            messenger.janusz_send(jan.ask_for_next_day(),sender)
        elif jan.state == "tomorrow":
            messenger.janusz_send(jan.ask_for_list_for_tomorrow(msg),sender)
        elif jan.table(msg) is True:
            messenger.janusz_send("Sending a table ....",sender)
            messenger.janusz_send_url(jan.send_table(),sender)
        elif jan.is_show(msg) is True:
            messenger.janusz_send_list(jan.show_habits(),sender)
        elif jan.is_add(msg) is True:
            print(jan.ask_for_tag())
            messenger.janusz_send(jan.ask_for_tag(),sender)
        elif jan.is_add_tag(msg) is True:
            messenger.janusz_send(jan.add_habit(msg, jan.tag_add_answer),sender)
        elif jan.is_delete(msg) is True:
            messenger.janusz_send(jan.delete_habits(msg),sender)
        elif jan.is_not_done(msg) is True:
            messenger.janusz_send_list(jan.what_not_done(),sender)
        elif jan.ask_habits(msg) is True:
            messenger.janusz_send(jan.janusz_response(),sender)
        elif jan.ask_tag_habits(msg) is True:
            messenger.janusz_send(jan.janusz_response(),sender)
        elif jan.is_yes(msg) is True:
            messenger.janusz_send(jan.janusz_response(),sender)
        elif jan.is_no(msg) is True:
            messenger.janusz_send(jan.janusz_response(),sender)
        elif jan.joke_response(msg) is True:
            messenger.janusz_send(jan.no_joke,sender)
        elif jan.is_show_stats(msg) is True:
            print("Recent Stats", jan.stats_days(msg))
            messenger.janusz_send_list(jan.show_stats(jan.stats_days(msg)),sender)
        elif jan.is_reset_person_questions(msg) is True:
            print("Reseting history")
            messenger.janusz_send(jan.reset_person_questions(),sender)
        else:
            messenger.handle(request.get_json(force=True))
    return ''

def ask_morning():
    for k in janusze:
        print("cron")
        jan = janusze[k]
        messenger.janusz_send(jan.new_day(),k)
        messenger.janusz_send(jan.janusz_response(),k)


if __name__ == '__main__':

    app.apscheduler.add_job(func=ask_morning, trigger='cron', hour = 8, minute= 45, args=[], id='j1')

    app.run(ssl_context='adhoc', use_reloader = False)

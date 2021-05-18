# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = '683e87d94bfd4c032c40164eb26d3c5d'
channel_access_token = 'FCDhYxaGG1PNpKLIlc1smwVjfH6vzXKp4XUYNystg09g0hlFyl4peur2cPg95+lRuZRBuFrl2ObDqdjqv2jTyB0edgqgFK1Z3dqw10BOnbHF4ldDGoTAO/O+Ud1qGp869gogC5M1tSbsbvo4dnU0YgdB04t89/1O/w1cDnyilFU='
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        if event.message.text in ['你是誰','妳是誰']:
            message = '我是目前就讀臺灣科技大學資管所碩一的學生李皓凱，主要研究領域為NLP，但我對CV也非常有興趣，曾時做了拿下ImageNet SOTA的論文「Noisy Student」。'
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
            )    

        response_text = event.message.text + '測試'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    return 'OK'


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)


#to see log
#heroku logs --tail --app line-tech-fresh-hank
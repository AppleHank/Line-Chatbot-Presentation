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
from flask import g
import os
import sys
from argparse import ArgumentParser
import configparser
from PIL import Image
from requests import post
import base64
from datetime import timedelta

from flask import Flask, request, abort, session
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
)
from linebot.models.messages import ImageMessage

app = Flask(__name__)


# get channel_secret and channel_access_token from your environment variable
config = configparser.ConfigParser()
config.read('config.ini')

channel_secret = config.get('line-bot', 'channel_access_token')
channel_access_token = config.get('line-bot', 'channel_secret')
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)



user_image_path = os.path.join(os.path.dirname(__file__),'facial_recog_dataset','user')
def make_user_img_dir():
    print(f'user_image_path:{user_image_path}')
    try:
        os.makedirs(user_image_path)
        print("successful create user image dir")
    except OSError as e:
        print('create user image dir error')
        print(f"error : {e}")
        pass

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    follow_buttons_template = ButtonsTemplate(
            title='皓凱Chatbot', text='透過以下按鈕了解我!', actions=[
                MessageAction(label='你是誰', text='你是誰'),
                MessageAction(label='履歷', text='履歷'),
                MessageAction(label='經歷 / 作品', text='經歷 / 作品'),
                MessageAction(label='臉部辨識/情緒分析 模型Demo', text='作品Demo'),
            ])
    template_message = TemplateSendMessage(
        alt_text='了解我', template=follow_buttons_template)
    line_bot_api.reply_message(event.reply_token, template_message)

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    text = event.message.text

    if text == '你是誰':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='我是目前就讀臺灣科技大學資管所碩一的學生李皓凱，主要研究領域為NLP，對CV領域也有極大興趣，例如我實作過ImageNet上的SOTA論文「Noisy Student」。')
        )

    elif text == '履歷':
        url = 'https://drive.google.com/file/d/1qLWDvFJPEprXXH7RYa23Hrk51-H2Iwkq/view?usp=sharing'
        img_url = request.url_root + '/static/Hank_Resume.jpg'
        messages = [
            TextSendMessage(text=f'PDF檔案連結:{url}'),
            ImageSendMessage(img_url,img_url)
        ]
        line_bot_api.reply_message(
            event.reply_token, messages
            )

    elif text == '經歷 / 作品':
        buttons_template = ButtonsTemplate(
        title='皓凱Chatbot', text='經歷', actions=[
            MessageAction(label='工作經歷', text='工作經歷'),
            MessageAction(label='參賽經歷', text='參賽經歷'),
            MessageAction(label='作品', text='作品'),
        ])
        template_message = TemplateSendMessage(
            alt_text='經歷與作品', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    elif text == '工作經歷':
        response_text = '尚未撰寫，馬上補上！'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    elif text == '參賽經歷':
        response_text = '尚未撰寫，馬上補上！'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    elif text == '作品':
        response_text = '尚未撰寫，馬上補上！'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    elif text == '作品Demo':
        response_text = TextSendMessage(text='將展示「人臉相似度比對」以及「臉部情緒分析」作品，請選擇模式。\n(github : https://github.com/AppleHank/FaceNet)')
        buttons_template = ButtonsTemplate(
        title='皓凱Chatbot', text='作品Demo選單', actions=[
            MessageAction(label='人臉相似度', text='人臉相似度'),
            MessageAction(label='臉部情緒分析', text='臉部情緒分析'),
        ])
        template_message = TemplateSendMessage(
            alt_text='作品Demo', template=buttons_template)

        messages = [
            response_text,
            template_message
        ]
        line_bot_api.reply_message(
            event.reply_token,
            messages
        )

    elif text == '人臉相似度':
        response_text = '請上傳一張照片，將會與四名藝人比較相似度'

        print('user:')
        print(event.source.user_id)
        url = 'http://140.118.109.198:3000/' #IP from my lab, I build a server to process facial recognition
        data = {'request_mode':'set','demo_mode':'facial_recognition','user':event.source.user_id}
        resp = post(url=url, json=data)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    elif text == '臉部情緒分析':
        response_text = '請上傳一張照片，將會分析屬於 「正常 / 開心 / 生氣」 其中一種情緒'

        url = 'http://140.118.109.198:3000/' #IP from my lab, I build a server to process facial recognition
        data = {'request_mode':'set','demo_mode':'emotion_recognition','user':event.source.user_id}
        resp = post(url=url, json=data)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

    elif text == '想了解':
        follow_buttons_template = ButtonsTemplate(
        title='皓凱Chatbot', text='透過以下按鈕了解我!', actions=[
            MessageAction(label='你是誰', text='你是誰'),
            MessageAction(label='履歷', text='履歷'),
            MessageAction(label='經歷 / 作品', text='經歷 / 作品'),
            MessageAction(label='臉部辨識/情緒分析 模型Demo', text='作品Demo'),
        ])
        template_message = TemplateSendMessage(
            alt_text='了解我', template=follow_buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='沒有聊天功能哦QQ 如果想要了解我，請輸入「想了解」')
        )   


def get_response(url,path,event,mode):
    data = {}
    data['request_mode'] = 'get'
    data['mode'] = mode
    with open(path,'rb') as img:
        image = base64.b64encode(img.read()).decode('latin1')
        data['ProcessedImage'] = image    
    if mode == 'facial_recognition':
        data['top_n'] = 2 #Can't set over 3, because one top_n message will send one TextSendMessage and ImageSendMessage, if top_n = 3, will send 6 message, which exceed limiation of free line chatbot acount
    
    try:
        resp = post(url=url, json=data)
    except (ValueError, AttributeError):
        print('-'*100)
        message = TextSendMessage(text='無法捕捉臉部，請嘗試上傳更高解析度 / 確認臉部垂直於地面')
        line_bot_api.reply_message(
        event.reply_token, message)
        return None
    return resp

def get_reply_list(data):
    reply_list = []
    top_similarity = data['similarity'] # <tuple> (<str> name of a similar star, <int> similarity score between 0 to 100)
    # row_images = data['pictures'] # base64 data
    file_names = data['names']
    eng_name_to_chinese = {'ihow':'劉以豪','chenwu':'金城武','user':'user','jaychou':'周杰倫','chi0':'林志玲'}
    for index,(file_name,similarity) in enumerate(zip(file_names,top_similarity)):
        star_name_eng = similarity[0]
        star_name_chi = eng_name_to_chinese[star_name_eng]
        img_url = request.url_root + '/static/' + star_name_eng + '/' + file_name
        print(f"img_url : {img_url}")
        reply_list.append(TextSendMessage(text=f"第 {index+1} 高相似度的藝人 : {star_name_chi}，相似度 : {similarity[1]}"))
        reply_list.append(ImageSendMessage(img_url, img_url))
    return reply_list

@handler.add(MessageEvent, message=ImageMessage)
def message_image(event):
    ext = 'jpg'

    message_content = line_bot_api.get_message_content(event.message.id)
    make_user_img_dir()
    message_iter_content = message_content.iter_content()
    path = os.path.join('facial_recog_dataset','user',event.message.id+'.'+ext)
    with open(path, 'wb') as fd:
        for chunk in message_iter_content:
            fd.write(chunk)
    #-------------------------------------------------------------
    print('user:')
    print(event.source.user_id)
    url = 'http://140.118.109.198:3000/' #IP from my lab, I build a server to process facial recognition
    mode = post(url=url,json={'request_mode':'retrieve','user':event.source.user_id}).json()['mode']
    print(mode)
    resp = get_response(url,path,event,mode)
    print(resp)
    if resp is None:
        print('is None')
        return
    
    data = resp.json()
    print(f"data:  {data}")
    if mode == 'facial_recognition':
        message = get_reply_list(data)
    elif mode == 'emotion_recognition':
        text = f"分析情續：{data['emotion']}"
        message = TextSendMessage(text=text)
    print(f"message: {message}")

    line_bot_api.reply_message(
        event.reply_token, message)



if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)

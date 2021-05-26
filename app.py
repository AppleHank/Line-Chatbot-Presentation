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
from requests.exceptions import ConnectionError
import base64
from datetime import timedelta
import json

from flask import Flask, request, abort, session
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, ButtonsTemplate, MessageAction, URIAction
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

def get_rasa_url():
    return 'http://140.118.109.198:5005/webhooks/rest/webhook'

def get_server_url():
    return 'http://140.118.109.198:3000/'#IP from my lab, I build a server to process facial recognition

def set_demo_mode(demo_mode,event):
    url =  get_server_url()
    data = {'request_mode':'set','demo_mode':demo_mode,'user':event.source.user_id}
    resp = post(url=url, json=data)

def get_CV_demo_message(text):
    response_text = TextSendMessage(text=text)
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
    return messages
    
def get_info_message(text):
    response_text = TextSendMessage(text=text)
    follow_buttons_template = ButtonsTemplate(
        title='皓凱Chatbot', text='透過以下按鈕了解我!', actions=[
            MessageAction(label='你是誰', text='你是誰'),
            MessageAction(label='我想看履歷', text='履歷'),
            MessageAction(label='我想看實習經歷 / 作品', text='實習經歷 / 作品'),
            MessageAction(label='臉部辨識/情緒分析 Demo', text='作品Demo'),
            MessageAction(label='RASA Chatbot Demo', text='RASA Demo')
        ])
    template_message = TemplateSendMessage(
        alt_text='了解我', template=follow_buttons_template)

    
    messages = [
        response_text,
        template_message
    ]
    return messages

def get_sever_answer(url,path,event,mode):
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
    except ConnectionError:
        response_text = '無法連接Server! 請通知Hank'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )
        return None

    if resp.status_code != 200:
        response_text = '無法捕捉臉部，請嘗試上傳更高解析度 / 確認臉部垂直於地面'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )
        return None

    return resp

def get_carousel_columns(data):
    carousel_columns = []
    top_similarity = data['similarity'] # <tuple> (<str> name of a similar star, <int> similarity score between 0 to 100)
    file_names = data['names']
    eng_name_to_chinese = {'ihow':'劉以豪','chenwu':'金城武','user':'李皓凱','jaychou':'周杰倫','chi0':'林志玲'}
    for index,(file_name,similarity) in enumerate(zip(file_names,top_similarity)):
        star_name_eng = similarity[0]
        star_name_chi = eng_name_to_chinese[star_name_eng]
        img_url = request.url_root + '/static/' + star_name_eng + '/' + file_name
        score = similarity[1]
        carousel_columns.append(CarouselColumn(
            thumbnail_image_url=img_url,
            text=(str)(score)+' / 100', 
            title=star_name_chi, 
            actions=[
                URIAction(label=f'搜尋{star_name_chi}', uri=f'https://www.google.com/search?q={star_name_chi}'),
            ]
        ))
    return carousel_columns

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

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
    set_demo_mode('default',event)

    text = '你好，這個聊天機器人是由 李皓凱 為了Line Tech Fresh實習所製作，目前有以下功能：'
    messages = get_info_message(text)
    app.logger.info("Got Follow event:" + event.source.user_id)
    
    line_bot_api.reply_message(event.reply_token, messages)

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    text = event.message.text

    if text == '你是誰':
        response_text = '我是目前就讀【臺灣科技大學】【資管所碩一】的學生【李皓凱】，【主要研究領域為NLP】，對【CV領域也有極大興趣】，例如我實作過ImageNet上的SOTA論文【Noisy Student】。'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    elif text == '履歷':
        url = 'https://drive.google.com/file/d/1qLWDvFJPEprXXH7RYa23Hrk51-H2Iwkq/view?usp=sharing'
        img_url = request.url_root + '/static/Hank_Resume.jpg'
        response_text = f'PDF檔案連結:{url}'
        messages = [
            TextSendMessage(text=response_text),
            ImageSendMessage(img_url,img_url)
        ]
        line_bot_api.reply_message(event.reply_token, messages)

    #-------------------------------Experiences-------------------------------
    elif text == '實習經歷 / 作品':
        buttons_template = ButtonsTemplate(
            title='皓凱Chatbot', text='經歷', actions=[
                MessageAction(label='想了解工作經歷', text='工作經歷'),
                MessageAction(label='想了解作品集', text='作品集'),
            ])
        template_message = TemplateSendMessage(
            alt_text='經歷與作品', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    elif text == '工作經歷':
        response_text = '------- 國泰世華銀行 | DDT - MLOps Intern -------\n \
任職期間，我擔任組長與組員在【AWS與GCP上開發兩個ML專案】，分別為【預測部門部屬的服務的流量】與【於門禁系統以人臉辨識取代刷卡辨識】。\n \
在技術方面，我負責了【資料蒐集、資料前處理、模型選擇、模型訓練、雲端平台Survey】。\n \
我也負責與Mentor溝通，主持組內的daily scrum，統整進度，控管專案時程。\n \
\n------------- 碩軟 | Data Analyst Intern -------------\n \
碩軟是與微軟合作的外商公司，在我任職期間我【獨自接下了一個客戶的專案】，這個專案會使用到Azure OCR服務，但若只使用OCR，準確率約只有80%。\
但【我將OCR與我設計的模型結合】，【運用NLP的方式】成功將準確率【提升至98%以上】，成功完成專案。\n \
\n------- 芬格遊戲 | software enginner Intern -------\n \
我與組員參加芬格公司舉辦的遊戲開發競賽，擔任組內唯一一個工程師，【自學所有技術】並【獨自撰寫約莫兩萬行的所有程式碼】，被公司從十幾組中選為唯一一組接受輔導，嘗試將遊戲上架的組別。\
'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    #-------------------------------Porjects-------------------------------
    elif text == '作品集':
        response_text = '請選擇NLP作品或CV作品'
        response_text = TextSendMessage(text=response_text)
        buttons_template = ButtonsTemplate(
            title='皓凱Chatbot', text='作品選單', actions=[
                MessageAction(label='想了解NLP作品', text='BERT for IR'),
                MessageAction(label='想了解CV作品', text='Noisy Student'),
            ])
        template_message = TemplateSendMessage(
            alt_text='作品', template=buttons_template)
        messages = [
            response_text,
            template_message
        ]
        line_bot_api.reply_message(event.reply_token, messages)

    elif text == 'BERT for IR':
        response_text = '------ BERT for Informaiton Retrieval(IR) ------\n\
我實作了搜尋引擎，將【BERT、XLNet、RoBERTa】等語言模型【融入傳統的IR模型BM25】，成功【將準確率提升約莫10%】。\n\
github:https://github.com/AppleHank/Bert-for-IR\n\
\n\
[任務目標]\n\
輸入一串sequence，輸出top-1000關聯的文章\n\
\n\
[資料集]\n\
200筆Query + 100,000篇網頁(Document)\n\
\n\
[作品介紹]\n\
在IR領域中，由於每一個Query(搜尋的關鍵字)的正相關樣本(有關聯的網頁)數量通常不到一百筆，對Deep Learning來說是非常不夠的，因此Depp Learning的模型在IR領域中往往不比傳統的方法來的好。\n \
因此我將重心擺在傳統模型BM25，對於每一筆Query都先計算出所有網頁的分數，取出top-1000後再將這些網頁以【Multiple Choice】的方式訓練BERT。最後再將訓練出的BERT和BM25 ensemble，成功在校內的Kaggle比賽獲得第三名。\n \
\n\
[訓練技巧]\n\
BERT的input長度限制512個token，但一篇文章動輒上千個文字，導致無法將所有token放入BERT。\
為了解決這個問題，我使用一個長度512的sliding window，對於每一篇文章都只擷取這個sliding window底下的文字當成文章，並使用BM25計算分數後移動sliding window，最後將分數最高的windwo視為這篇文章，丟進BERT。\
'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    elif text == 'Noisy Student':
        response_text = '------ Noisy Student ------\n\
我實作了ImageNet上的SOTA論文 【Noisy Student】，成功透過【semi-supervise】的方式運用Unlabeled Data，【配合Distilation的方式將準確率提升20%】。\n \
github:https://github.com/AppleHank/Noisy-Student_sample\n\
\n\
[任務目標]\n\
輸入一張圖片，輸出圖片類別(11種)\n\
\n\
[資料集]\n\
Food-11，11種食物的分類資料，3,000張labeled data, 6000張unlabeled data\n\
\n\
[作品介紹]\n\
Noisy Student是2020年由Google提出的CV領域的論文，是近期較具指標性的semi-supervised learning的方式，也在當時拿下了ImageNet上的SAOTA。\
我將作品實作於食物分類資料集，先使用labeled data訓練出第一代Teacher Model，利用Teacher Model在unlabeled data上產生pseudo-labeled data，同時考慮imbalance的問題。\
接著再將pseudo-labeled data與labeled data結合，利用這些data訓練第一代的Student Model，訓練結束後再將Student Model變為第二代的Teacher Model，如此疊帶的去訓練，最終從第一代的64%準確率提升至84%。\
'

        G1_url = request.url_root + '/static/noisy_student/G_1_OK.png'
        G5_url = request.url_root + '/static/noisy_student/G_5_OK.png'
        messages = [
            TextSendMessage(text=response_text),
            ImageSendMessage(G1_url,G1_url),
            ImageSendMessage(G5_url,G5_url),
        ]

        line_bot_api.reply_message(event.reply_token, messages)

    #-------------------------------Demo-------------------------------
    elif text == '作品Demo':
        text = '將展示【人臉相似度比對】以及【臉部情緒分析】作品，請選擇模式。\ngithub : https://github.com/AppleHank/FaceNet'
        messages = get_CV_demo_message(text)

        line_bot_api.reply_message(event.reply_token, messages)

    elif text == '人臉相似度':
        response_text = '請上傳一張照片，將會與四名藝人比較相似度，上傳後請稍等約五秒'
        set_demo_mode('facial_recognition',event)

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    elif text == '臉部情緒分析':
        response_text = '請上傳一張照片，將會分析屬於 【正常 / 開心 / 生氣】 其中一種情緒，上傳後請稍等約五秒'
        set_demo_mode('emotion_recognition',event)    

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    #-------------------------------RASA-------------------------------
    elif text == 'RASA':
        response_text = "請輸入英文！目前支援情境為\n1.詢問你是誰(who are you?)\n2.想了解關於我更多的資訊(Tell me more about you)\n3.安慰情緒(I'm sad)"
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    elif isEnglish(text):
        url = get_rasa_url()
        data = {
            "sender": event.source.user_id,  
            "message": text
        }

        try:
            resp = post(url=url,data=json.dumps(data))
            response_text = ''
            messages = []
            for response_info in  resp.json():
                if 'text' in response_info:
                    messages.append(TextSendMessage(text=response_info['text']))
                elif 'image' in response_info:
                    url = response_info['image']
                    messages.append(ImageSendMessage(url,url))
                else:
                    messages.append(TextSendMessage(text='這句回覆出了點差錯，沒辦法正常顯示QQ'))
            
        except ConnectionError:
            response_text = '無法連接Server! 請通知Hank'
            messages = [TextSendMessage(text=response_text)]

        line_bot_api.reply_message(
            event.reply_token, messages
        )

    #-------------------------------Others-------------------------------
    else:
        response_text = '沒有中文聊天功能哦QQ，最新版本加入了非常簡易的【RASA Chatbot英文版本Demo】，輸入英文詢問我是誰/我的經歷可以得到簡易回答！也可以分享你的情緒給Chatbot哦！\n\n\
或是如果想要了解我，歡迎點選下方按鈕！'
        messages = get_info_message(response_text)

        line_bot_api.reply_message(event.reply_token, messages)   

@handler.add(MessageEvent, message=ImageMessage)
def message_image(event):
    
    url = get_server_url()
    mode = post(url=url,json={'request_mode':'retrieve','user':event.source.user_id}).json()['mode']
    if mode == 'default':
        text = '若想使用CV相關demo，請選擇以下模式'
        messages = get_CV_demo_message(text)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    #save temp file
    ext = 'jpg'
    message_content = line_bot_api.get_message_content(event.message.id)
    make_user_img_dir()
    path = os.path.join('facial_recog_dataset','user',event.message.id+'.'+ext)
    with open(path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    #-----------------------------retrieve predict answer from server--------------------------------
    resp = get_sever_answer(url,path,event,mode)
    if resp is None: #if no face detected or server not available
        return
    data = resp.json()
    if mode == 'facial_recognition':
        columns = get_carousel_columns(data)
        carousel_template = CarouselTemplate(columns=columns)
        message = TemplateSendMessage(
            alt_text='比對結果', template=carousel_template)

    elif mode == 'emotion_recognition':
        response_text = f"分析情緒：{data['emotion']}"
        message = TextSendMessage(text=response_text)

    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)

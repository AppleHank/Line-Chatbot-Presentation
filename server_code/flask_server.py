import json
from flask import Flask,request     
import facial_recognition_model
import facial_emotion_model
from PIL import Image                                           
import base64
import io

app = Flask(__name__)
user_dict = {}
@app.route('/', methods=['POST'])
def result():
    print('enter')
    global user_dict
    
    try:
        datas = json.loads(request.get_data())
        print(datas)
        if 'request_mode' in datas:
            if datas['request_mode'] == 'set':
#                 if datas['user'] not in user_dict:
                user_dict[datas['user']] = datas['demo_mode']
                return {'mode':user_dict[datas['user']]}
            elif datas['request_mode'] == 'retrieve':
                print(user_dict)
                return {'mode':user_dict[datas['user']]}
            
        
        row_image = datas['ProcessedImage']
        msg = base64.b64decode(row_image)
        buf = io.BytesIO(msg)
        image = Image.open(buf)
        
        if 'top_n' in datas:
            top_n = datas['top_n']
        
    except (ValueError, KeyError, TypeError, LookupError) as e:
        print(e)
        error_message = {'status' : 400
                        ,'message' : "ocr result error! check your input file."}
        return json.loads(json.dumps(error_message))
    
    if datas['mode'] == 'facial_recognition':
        top_n = facial_recognition_model.similarity_recognition(image,'facial_recog_dataset',top_n=top_n)
        return json.dumps(top_n)
    elif datas['mode'] == 'emotion_recognition':
        emotion = facial_emotion_model.emotion_recognition(image,print_prob=True)
        return emotion
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

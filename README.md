# Line-Chatbot-Presentation
## 簡介
這是一個使用透過Flask將服務架在Heroku上的Line Chatbot，將Chatbot加入好友後會有基本的Follow Event指引使用者，傳送一個botton template給使用者，選項包含「你是誰」、「我想看履歷」、「我想看實習經歷 / 作品」、**「臉部辨識/情緒分析Demo」**。<br />
除了上述功能以外，在5月26也加入了**RASA英文Chatbot**，能夠進行簡單的對話

## 臉部辨識/情緒分析
使用者若想使用此功能，可透過下面兩種方式
- 點選「臉部辨識/情緒分析Demo」按鈕
- 直接上傳一張圖片

Chatbot將會傳送一個botton template給使用者，選擇要使用「人臉相似度比較」功能 或是 「臉部情緒分析」功能，點選後並傳送圖片後，將會將圖片傳至我所架設的Server進行處理並傳回結果。

### 人臉相似度比較
傳送一張包含人臉的圖片，傳回與藝人們(還有我自己)的相似度(0~100%)<br />
- 實作<br />
我使用2016年人臉辨識的SOTA模型「FaceNet」，先將原始圖片(Query Image)透過「MTCNN模型」抓取臉部影像，在將臉部影像輸入pretrain在西方人臉資料集的「Inception ResnetV1模型」，Inception將會回傳512維度的Embedding。<br />
得到Query Image的Embedding後，我再將「預先準備好的藝人和我的圖片」計算Embedding，最後將Query Image的Embedding和這些圖片的Embedding計算Cosine Similarity，得到相似度後回傳。<br />
![facial recognition](https://github.com/AppleHank/Line-Chatbot-Presentation/blob/main/ReadMe_images/187436527_319387753111581_6003927579262384847_n_smaller.png)
<br />

### 情緒分析
傳送一張包含人臉的圖片，回傳屬於「正常，開心，生氣」其中一種情緒<br />
- 實作<br />
我將「人臉相似度比較」中的FaceNet接上一個Fully-Connected-layer，將512維縮放至3維度，並使用AffectNet資料集訓練模型。在前處理時，由於資料集部分人臉比例過大，無法被MTCNN有效捕捉，因此我將輸入圖片先padding後再輸入模型訓練，解決無法捕捉人臉的問題。<br />
![emotion recognition](https://github.com/AppleHank/Line-Chatbot-Presentation/blob/main/ReadMe_images/188656919_495260258565990_4620626799712487533_n_smaller.jpg)

### RASA英文Chatbot
輸入英文文字，回傳聊天機器人的回應<br />
- 介紹<br />
RASA Chatbot是開源的Natural-language understanding聊天機器人，透過Named Entity Recognition(NER)以及Intention Recognition兩個任務來訓練Chatbot。<br />
我透過RASA API將我訓練好的RASA Chatbot部屬在我的Server，透過Http Request傳送使用者的訊息給RASA，取得結果後在回傳給使用者。
- 支援的話題<br />
以下為訓練好的Intention，可輸入類似語句，都能傳回一樣的結果。
  1. 詢問你是誰(who are you?)
  2. 想了解關於我更多的資訊(Tell me more about you)
![RASA](https://github.com/AppleHank/Line-Chatbot-Presentation/blob/main/ReadMe_images/111230_smaller.jpg)

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from bs4 import BeautifulSoup
import requests,re
import configparser
import random
from linebot.models import *

app = Flask(__name__)

bible_abrev_math = ['1Sa','2Sa','1Ki','2Ki','1Ch','2Ch','1Co','2Co','1Ts','2Ts','1Ti','2Ti','1Pe','2Pe','1Jn','2Jn','3Jn']

config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
google_access_key = config['google_api']['Google_Access_Key']
playlist_ID = config['google_api']['Youtube_Playlist']
QR_Code_URL =  config['line_add_friend_QR_code']['QR_Code_URL']

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

def banner_church_news():
    return_message = ""
    domain = "http://www.bannerch.org"
    html = requests.get(domain + "/news/latest-news.html").content
    soup = BeautifulSoup(html)
    for post_struct in soup.find_all('h3', class_="post-title"):
        return_message += post_struct.a.text + "\n" + domain + post_struct.a['href'] + "\n"
    return return_message.strip()

def banner_church_evidence():
    return_message = ""
    domain = "http://www.bannerch.org"
    html = requests.get(domain + "/media-zone/story.html").content
    soup = BeautifulSoup(html)
    for post_struct in soup.find_all('div', class_= "post-info"):
        return_message += post_struct.a.text + "\n" + domain + post_struct.a['href'] + "\n"
    return return_message.strip()

def bible_chapter_ref():
    bible_ref = {}
    with open("bible_ref.txt") as f:
        bible_ref_txt = f.read()
    for bible_ref_txt_line in bible_ref_txt.split("\n"):
        bible_ref_txt_result = bible_ref_txt_line.split()
        bible_ref[bible_ref_txt_result[0]] =bible_ref_txt_result[2] 
        bible_ref[bible_ref_txt_result[1]] =bible_ref_txt_result[2] 
        bible_ref[bible_ref_txt_result[2]] =bible_ref_txt_result[2] 
    return bible_ref

def bible_eng_to_ch():
    bible_ref = {}
    with open("bible_ref.txt") as f:
        bible_ref_txt = f.read()
    for bible_ref_txt_line in bible_ref_txt.split("\n"):
        bible_ref_txt_result = bible_ref_txt_line.split()
        bible_ref[bible_ref_txt_result[2]] =bible_ref_txt_result[0]
    return bible_ref

def load_bible_from_txt():
    txt = ""
    bible_dict = {}
    with open("bible_utf8") as f:
        txt = f.read()
    for txt_line in txt.split("\n"):
        (book, chapter_section, content) = txt_line.split(" ")
        chapter, section = chapter_section.split(":")
        content = content.replace("\u3000"," ")
        if book not in bible_dict:
            bible_dict[book] = []
        bible_dict[book].append((int(chapter), int(section), content))
    return bible_dict

def search_by_book_ch(search_text):
    message = ""
    search_text_list = search_pattern(search_text)
    book = search_text_list[0]
    if book in bible_chapter_dict:
        book = bible_chapter_dict[book]
    if book in bible_dict:
        if len(search_text_list) < 3:
            for (ch_bible, sec_bible, content) in bible_dict[book]:
                if len(search_text_list) == 2 and ch_bible == search_text_list[1]:
                    message += str(ch_bible) + ":" + str(sec_bible) + " " + content + "\n"
        else: 
            (book, ch, sec) = (book, search_text_list[1], search_text_list[2])
            for (ch_bible, sec_bible, content) in bible_dict[book]:
                if int(ch) == ch_bible and int(sec) == sec_bible:
                    message = content
                    break
    return message

def church_imagercy():
    return "旌旗教會將從台灣並中國大陸差派出成千上萬的宣教士，是一支龐大而強勁的宣教軍隊，足跡踏遍中國、亞洲、世界許多福音未得之地，贏得靈魂歸主，且成全聖徒、各盡其職，在各處建立剛強榮耀的教會，宣告神國度的禧年，使遍地充滿神的榮耀。" + "\n" + "https://www.youtube.com/watch?v=6GwKI-Vxn90"

def church_dedication():
    return "http://www.bannerch.org/give/dedication.html"

def random_bible_sentence():
    book = random.choice(list(bible_dict))
    sentence_tuple = random.choice(bible_dict[book])
    return e_to_c_dict[book] +" " + str(sentence_tuple[0]) + ":" + str(sentence_tuple[1]) + " " + str(sentence_tuple[2])

def load_music_from_youtube():
    r = requests.get(url='https://www.googleapis.com/youtube/v3/playlistItems?playlistId=' + playlist_ID + '&maxResults=50&part=snippet%2CcontentDetails&key=' + google_access_key)
    playlist_json = r.json()
    played_music_dict = {}
    for play_item in playlist_json['items']:
        played_music_dict[play_item['snippet']['title']] = 'https://www.youtube.com/watch?v=' + play_item['contentDetails']['videoId']
    return played_music_dict

def random_choice_music():
    return_music_title = random.choice(list(music_dict))
    return return_music_title + "\n" + music_dict[return_music_title]

def search_pattern(search_string):
    book_list = []
    need_to_find_book = True
    for bam in bible_abrev_math:
        if bam in search_string:
            search_string = search_string.replace(bam, "").strip()
            book_list.append(bam)
            need_to_find_book = False
            break
    if need_to_find_book:
        book_list = re.findall("[\u4e00-\u9fa5a-zA-Z]+", search_string)
    ch_sec_list = re.findall("[\d]+",search_string)
    if len(ch_sec_list) == 1:
        return (book_list[0] ,int(ch_sec_list[0]))
    else:
        return (book_list[0] ,int(ch_sec_list[0]) ,int(ch_sec_list[1]))

def video_template():
    return TemplateSendMessage(
                alt_text='影片 template',
                template=ButtonsTemplate(
                    title='主日影片 & 見證影片',
                    text='請選擇',
                    thumbnail_image_url='https://1.bp.blogspot.com/-J5clb3IYsUE/Tjzm7tIgPXI/AAAAAAAAAbs/R8Dy1s5BT-o/s1600/4582085320_71aa29bc70_o.jpg',
                    actions=[
                        URITemplateAction(
                        label='主日影片',
                        uri='https://www.youtube.com/user/bannerch'
                        ),
                        MessageTemplateAction(
                            label='見證影片',
                            text='見證'
                        )
                    ]
                )
            )

def add_friend_QR_Code():
    return ImageSendMessage(
            original_content_url = QR_Code_URL,
            preview_image_url = QR_Code_URL
        )

@handler.add(MessageEvent, message = TextMessage)
def handle_message(event):
    message_text = event.message.text.lower().title().strip()
    if message_text in ["影片", "新聞", "見證", "奉獻", "異象", "抽經文", "抽詩歌","加好友"]:
        if message_text == "影片":
            line_bot_api.reply_message(event.reply_token, video_template())
        elif message_text == "新聞":
            message = banner_church_news()
        elif message_text == "見證":
            message = banner_church_evidence()
        elif message_text == "奉獻":
            message = church_dedication()
        elif message_text == "異象":
            message = church_imagercy()
        elif message_text == "抽經文":
            message = random_bible_sentence()
        elif message_text == "抽詩歌":
            message = random_choice_music()
        elif message_text == "加好友":
            line_bot_api.reply_message(event.reply_token, add_friend_QR_Code())
    else:
        if search_pattern(message_text)[0] in bible_chapter_dict:
            message = search_by_book_ch(message_text)
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = message))

bible_chapter_dict = bible_chapter_ref()
bible_dict = load_bible_from_txt()
music_dict = load_music_from_youtube()
e_to_c_dict = bible_eng_to_ch()

if __name__ == "__main__":
    app.run()
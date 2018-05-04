
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

app = Flask(__name__)

config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
google_access_key = config['google_api']['Google_Access_Key']
playlist_ID = config['google_api']['Youtube_Playlist']
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
        #print(post_struct.a.text)
        #print(domain + post_struct.a['href'])
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

bible_chapter_dict = bible_chapter_ref()

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

bible_dict = load_bible_from_txt()

def search_by_book_ch(search_text):
    message = "No content"
    search_text_list = re.split("[^\u4e00-\u9fa5\w\d]",search_text)
    if len(search_text_list) == 1:
        book = search_text_list[0]
        if book in bible_chapter_dict:
            book = bible_chapter_dict[book]
        if book in bible_dict:
            message = ""
            for (ch_bible, sec_bible, content) in bible_dict[book]:
                message += str(ch_bible) + ":" + str(sec_bible) + " " + content + "\n"
    else: 
        (book, ch, sec) = search_text_list
        if book in bible_chapter_dict:
            book = bible_chapter_dict[book]
        if book in bible_dict:
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
    return book +" " + str(sentence_tuple[0]) + ":" + str(sentence_tuple[1]) + " " + str(sentence_tuple[2])

def load_music_from_youtube():
    r = requests.get(url='https://www.googleapis.com/youtube/v3/playlistItems?playlistId=' + playlist_ID + '&maxResults=50&part=snippet%2CcontentDetails&key=' + google_access_key)
    playlist_json = r.json()
    played_music_dict = {}
    for play_item in playlist_json['items']:
        played_music_dict[play_item['snippet']['title']] = 'https://www.youtube.com/watch?v=' + play_item['contentDetails']['videoId']
    return played_music_dict

music_dict = load_music_from_youtube()

def random_choice_music():
    return_music_title = random.choice(list(music_dict))
    return return_music_title + "\n" + music_dict[return_music_title]

@handler.add(MessageEvent, message = TextMessage)
def handle_message(event):
    message_text = event.message.text.title()
    if message_text == "新聞":
        message = banner_church_news()
    elif message_text == "見證":
        message = banner_church_evidence()
    elif re.split("[^\u4e00-\u9fa5\w\d]", message_text)[0] in bible_chapter_dict:
        message = search_by_book_ch(message_text)
    elif message_text == "奉獻":
        message = church_dedication()
    elif message_text == "異象":
        message = church_imagercy()
    elif message_text == "抽經文":
        message = random_bible_sentence()
    elif message_text == "抽詩歌":
        message = random_choice_music()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
    app.run()
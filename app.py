#app.py
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, AudioSendMessage, 
    TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction
)

from linebot_function import en_dictionary
import config

app = Flask(__name__)

line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    word = event.message.text
    result = en_dictionary(word)
    print(result)
    text = word + '\nAudio: UK / US'

    line_bot_api.push_message(
        config.USER_ID, TextSendMessage(text=text))
    line_bot_api.push_message(
        config.USER_ID, \
        AudioSendMessage(original_content_url=result[0]['uk_audio'], duration=200))
    line_bot_api.push_message(
        config.USER_ID, \
        AudioSendMessage(original_content_url=result[0]['us_audio'], duration=200))

    for res in result:
        # try:
        message = dict_carousel(word, res['description'], res['part_of_speech'])
        line_bot_api.push_message(config.USER_ID, message)
        # except:
        #     line_bot_api.push_message(config.USER_ID, TextSendMessage(text='ERROR'))


def dict_carousel(word, description_result, part_of_speech):
    cols = []
    n = 0
    for result in description_result:
        if n >= 10:
            break

        text = '(' + part_of_speech + ')\n'
        for i in range(len(result['def'])):
            text += '{}. {}\n'.format(i+1, result['def'][i]['def_tw']) #, result['def'][i]['def_tw'])

            sentence = str()
            for j in range(len(result['def'][i]['sentences'])):
                sentence += result['def'][i]['sentences'][j]

        temp = {
            'title': result['guide_word'],
            'text': text,
            'sentence': sentence
        }
        cols.append(temp)
        n += 1

    print(cols)
    carousel_template_message = TemplateSendMessage(
        alt_text='dictionary carousel',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title=col['title'],
                    text=col['text'],
                    actions=[
                        MessageAction(
                            label='👆🏻例句',
                            text=col['sentence'])
                    ]) for col in cols]))
    return carousel_template_message

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
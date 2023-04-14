import openai
from googletrans import Translator
import os, path
import re

from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import settings
import voice_assistant as va


bot = Bot(token=settings.TG_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


openai.api_key = settings.GPT_KEY

translator = Translator()


@dp.message_handler(commands=['start', 'gpt'])
async def send_welcome(message: types.Message):
    await message.answer(
        text="Привет, теперь я поддерживаю и голос!\nЯ использую <b>GPT-3.5</b> и <b>DALL-E</b> для ответов на твои сообщения!\n\n"
             "• Начни свое сообщение с '<b>Бот,</b>' и я сгенерирую ответ.\n"
             "• Начни свое сообщение с '<b>Покажи </b>' и я сгенерирую картинку по твоему запросу.\n\n"
             "Например, напиши или скажи:\n"
             "<b>'Бот, сколько планет в солнечной системе?'</b>\nили\n<b>'Покажи Тверской театр драмы'</b>",
        parse_mode='html')


@dp.message_handler(Text(startswith=settings.call_list))
async def text_gpt_request(message: types.Message):
    sent = await message.answer("Подождите, я думаю...")
    try:
        user_question = message.text[4:].strip()
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_question}
            ],
            timeout=30
        )
        answer = response["choices"][0]["message"]["content"]
        await sent.edit_text(answer)
    except:
        await sent.edit_text(
            'Упс, что-то пошло не-так. Возможно не удалось установить связь с сервером, попробуйте позже')


# Запрос для использования GPT-3
# response = openai.Completion.create(
#     engine="davinchi-003",
#     prompt=user_question,
#     max_tokens=3000,
#     temperature=0.6,
#     timeout=60
# )
# answer = response.choices[0].text.strip()


@dp.message_handler(Text(startswith=settings.call_list_image))
async def image_gpt_request(message: types.message):
    sent = await message.answer("Подождите, я думаю...")
    try:
        user_question = message.text[7:].strip()
        print(user_question)
        user_question = translator.translate(user_question, dest='en').text
        print(user_question)
        response = openai.Image.create(
            prompt=user_question,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        await sent.edit_text(image_url)
    except:
        await sent.edit_text(
            'Упс, что-то пошло не-так. Возможно не удалось установить связь с сервером, попробуйте позже')


@dp.message_handler(content_types=[types.ContentType.VOICE])
async def voice_gpt_request(message: types.message):
    ogg_filepath = await va.download_voice_as_ogg(message.voice)
    mp3_filepath = va.convert_ogg_to_mp3(ogg_filepath)
    transcripted_text = va.convert_speech_to_text(mp3_filepath)
    print(transcripted_text)
    is_chat = re.search('^Бот', transcripted_text)
    is_image = re.search('^Покажи', transcripted_text)
    if (is_chat != None):
        sent = await message.answer("Подождите, я думаю...")
        transcripted_text = transcripted_text[4:].strip()
        print(transcripted_text)
        answer = va.generate_response(transcripted_text)
        print(answer)
        answer_voice_path = va.convert_text_to_speech(answer)
        answer_voice = types.InputFile(va.convert_text_to_speech(answer))
        print(answer_voice)
        await bot.delete_message(sent.chat.id, sent.message_id)
        await bot.send_voice(chat_id=sent.chat.id,
                             voice=answer_voice)
        os.remove(ogg_filepath)
        os.remove(mp3_filepath)
        os.remove(answer_voice_path)
    elif (is_image != None):
        sent = await message.answer("Подождите, я думаю...")
        try:
            transcripted_text = transcripted_text[7:].strip()
            print(transcripted_text)
            transcripted_text = translator.translate(transcripted_text, dest='en').text
            print(transcripted_text)
            user_question = transcripted_text
            response = openai.Image.create(
                prompt=user_question,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']

            await sent.edit_text(image_url)
        except:
            await sent.edit_text(
                'Упс, что-то пошло не-так. Возможно не удалось установить связь с сервером, попробуйте позже')
    else:
        text = f'<b>{message.from_user.first_name}</b>\n{transcripted_text}'
        await message.answer(text=text, parse_mode='html')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

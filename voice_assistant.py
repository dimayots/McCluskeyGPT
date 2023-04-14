import openai
import os
import pydub
import gtts


async def download_voice_as_ogg(voice):
    voice_file = await voice.get_file()
    ogg_filepath = os.path.join('recieved.ogg')
    await voice_file.download(ogg_filepath)
    return ogg_filepath


def convert_ogg_to_mp3(ogg_filepath):
    print(ogg_filepath)
    mp3_filepath = os.path.join('converted.mp3')
    print(mp3_filepath)
    audio = pydub.AudioSegment.from_file('recieved.ogg', format='ogg')
    print(audio)
    audio.export(mp3_filepath, format="mp3")
    return mp3_filepath


def convert_speech_to_text(audio_filepath):
    with open(audio_filepath, "rb") as audio:
        transcript = openai.Audio.transcribe("whisper-1", audio)
        return transcript["text"]


def generate_response(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    answer = response["choices"][0]["message"]["content"]
    return answer


def convert_text_to_speech(text, language_code='ru'):
    output_filepath = os.path.join('answer.ogg')
    tts = gtts.gTTS(text=text, lang=language_code)
    tts.save(output_filepath)
    return output_filepath

import logging
from aiogram import types
from pydub import AudioSegment
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import os
bot = None
class ConvertAudioMP3ToWAV(StatesGroup):
    waiting_for_audio = State()
class ConvertAudioWAVToMP3(StatesGroup):
    waiting_for_audio = State()
class ConvertAudioOGGToMP3(StatesGroup):
    waiting_for_audio = State()
class ConvertAudioOGGToWAV(StatesGroup):
    waiting_for_audio = State()

async def handle_audio(message: types.Message, state: FSMContext):
    try:
        # Получаем информацию о файле
        if(message.voice != None):
            file_id = message.voice.file_id
        else:
            file_id = message.audio.file_id
        # Получаем путь к файлу
        print(file_id)
        # Получаем путь к файлу
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        # Скачиваем файл
        downloaded_file = await bot.download_file(file_path)
        # Сохраняем MP3 файл локально
        mp3_filename = f"./Files/Audio/{file_id}.mp3"

        with open(mp3_filename, 'wb') as f:
            f.write(downloaded_file.read())
            await message.reply(f"Получен аудиофайл")

        input_mp3_path = f"./Files/Audio/{file_id}.mp3"
        output_wav_path = f"./Files/Audio/{file_id}.wav"
        audio = AudioSegment.from_mp3(input_mp3_path)
        audio.export(output_wav_path, format='wav', codec='pcm_s16le')
        await message.reply(f"Конверирован, высылаем")

            #bot.send_audio(message.chat.id, f)
            # Отправляем сконвертированный файл пользователю
        if(os.path.exists(output_wav_path)):
            if (os.path.getsize(output_wav_path) < 5000000):
                audio_file = FSInputFile(path=output_wav_path)
                await message.answer_audio(audio=audio_file)
                os.remove(input_mp3_path)
                os.remove(output_wav_path)
                await message.reply(f"Готово!")
            else:
                await message.reply(f"Файл слишком большой, максимальный размер 5мб")
        else:
            print("Файл не обнаружен")
    except Exception as e:
        await message.reply("Произошла ошибка при обработке аудиофайла.")
        logging.error(f"Ошибка обработки аудиофайла: {e}")
async def handle_audioWAVToMP3(message: types.Message, state: FSMContext):
    try:
        # Получаем информацию о файле
        file_id = message.document.file_id
        # Получаем путь к файлу
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        # Скачиваем файл
        downloaded_file = await bot.download_file(file_path)
        # Сохраняем WAV файл локально
        wav_filename = f"./Files/Audio/{file_id}.wav"
        with open(wav_filename, 'wb') as f:
            f.write(downloaded_file.read())
            await message.reply(f"Получен аудиофайл WAV")
        input_wav_path = f"./Files/Audio/{file_id}.wav"
        output_mp3_path = f"./Files/Audio/{file_id}.mp3"
        audio = AudioSegment.from_wav(input_wav_path)
        audio.export(output_mp3_path, format='mp3')
        # Отправляем сконвертированный файл пользователю
        if os.path.exists(output_mp3_path):
            if os.path.getsize(output_mp3_path) < 5000000:  # проверяем размер файла
                audio_file = FSInputFile(path=output_mp3_path)
                await message.answer_audio(audio=audio_file)
                os.remove(input_wav_path)
                os.remove(output_mp3_path)
                await message.reply(f"Готово!")
            else:
                await message.reply(f"Файл слишком большой, максимальный размер 5мб")
        else:
            print("Файл не обнаружен")
    except Exception as e:
        await message.reply("Произошла ошибка при обработке аудиофайла WAV -> MP3.")
        logging.error(f"Ошибка обработки аудиофайла WAV -> MP3: {e}")

async def handle_audioOggToMP3(message: types.Message, state: FSMContext):
    try:
        file_id = message.voice.file_id
        # Получаем путь к файлу
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        # Скачиваем файл
        downloaded_file = await bot.download_file(file_path)
        # Сохраняем WAV файл локально
        wav_filename = f"./Files/Audio/{file_id}.ogg"
        with open(wav_filename, 'wb') as f:
            f.write(downloaded_file.read())
            await message.reply(f"Получен аудиофайл OGG")
        input_wav_path = f"./Files/Audio/{file_id}.ogg"
        output_mp3_path = f"./Files/Audio/{file_id}.mp3"
        audio = AudioSegment.from_ogg(input_wav_path)
        audio.export(output_mp3_path, format='mp3')
        # Отправляем сконвертированный файл пользователю
        if os.path.exists(output_mp3_path):
            if os.path.getsize(output_mp3_path) < 5000000:  # проверяем размер файла
                audio_file = FSInputFile(path=output_mp3_path)
                await message.answer_audio(audio=audio_file)
                os.remove(input_wav_path)
                os.remove(output_mp3_path)
                await message.reply(f"Готово!")
            else:
                await message.reply(f"Файл слишком большой, максимальный размер 5мб")
        else:
            print("Файл не обнаружен")
    except Exception as e:
        await message.reply("Произошла ошибка при обработке аудиофайла OGG -> MP3.")
        logging.error(f"Ошибка обработки аудиофайла WAV -> MP3: {e}")

async def handle_audioOggToWav(message: types.Message, state: FSMContext):
    try:
        file_id = message.voice.file_id
        # Получаем путь к файлу
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        # Скачиваем файл
        downloaded_file = await bot.download_file(file_path)
        # Сохраняем WAV файл локально
        wav_filename = f"./Files/Audio/{file_id}.ogg"
        with open(wav_filename, 'wb') as f:
            f.write(downloaded_file.read())
            await message.reply(f"Получен аудиофайл OGG")
        input_wav_path = f"./Files/Audio/{file_id}.ogg"
        output_mp3_path = f"./Files/Audio/{file_id}.wav"
        audio = AudioSegment.from_wav(input_wav_path)
        audio.export(output_mp3_path, format='wav')
        # Отправляем сконвертированный файл пользователю
        if os.path.exists(output_mp3_path):
            if os.path.getsize(output_mp3_path) < 5000000:  # проверяем размер файла
                audio_file = FSInputFile(path=output_mp3_path)
                await message.answer_audio(audio=audio_file)
                os.remove(input_wav_path)
                os.remove(output_mp3_path)
                await message.reply(f"Готово!")
            else:
                await message.reply(f"Файл слишком большой, максимальный размер 5мб")
        else:
            print("Файл не обнаружен")
    except Exception as e:
        await message.reply("Произошла ошибка при обработке аудиофайла OGG -> WAV.")
        logging.error(f"Ошибка обработки аудиофайла WAV -> MP3: {e}")
        os.remove(input_wav_path)

import logging
from aiogram import types
import os
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from docx import Document  # Import Document from docx library
import mimetypes  # Import mimetypes for file type checking

class TextToFileClass(StatesGroup):
    waiting_for_file_info = State()

async def handle_text_to_file(message: types.Message, state: FSMContext):
    try:
        # Разделяем сообщение на имя файла и текст
        file_info = message.text.split('\n', 1)
        if len(file_info) != 2:
            await message.reply("Некорректный формат. Введите запрос по следующему примеру:\nfile.txt\nHello world!")
            await state.set_state(TextToFileClass.waiting_for_file_info)
            return
        file_name, file_content = file_info

        # Получаем расширение файла из имени
        file_extension = os.path.splitext(file_name)[1].lower()

        # Проверяем корректность имени файла
        if not file_name or not file_content:
            await message.reply("Некорректный формат. Введите запрос по следующему примеру:\nfile.txt\nHello world!")
            await state.set_state(TextToFileClass.waiting_for_file_info)
            return

        # Создаем файл
        if file_extension == ".docx":
            # Создаем и записываем DOCX файл
            doc = Document()
            doc.add_paragraph(file_content)
            file_path = file_name  # Используем имя файла без дублирования расширения
            doc.save(file_path)
            await message.reply(f"Файл '{file_name}' успешно создан и заполнен текстом.")
            docx_file = FSInputFile(file_path)
            await message.answer_document(docx_file)

        else:
            # Создаем текстовый файл
            file_path = file_name  # Используем имя файла без дублирования расширения
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(file_content)
            await message.reply(f"Файл '{file_name}' успешно создан и заполнен текстом.")
            text_file = FSInputFile(file_path)
            await message.answer_document(text_file)

        # Удаляем файл после отправки
        os.remove(file_path)

    except Exception as e:
        await message.reply("Произошла ошибка при создании файла.")
        logging.error(f"Ошибка при создании файла: {e}")
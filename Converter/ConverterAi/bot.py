import asyncio
import logging
import mimetypes
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.fsm.storage.memory import MemoryStorage
from pydub import AudioSegment
import sqlite3
from TextToFile import TextToFileClass
import TextToFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import datetime
from PIL import Image
import PIL
from moviepy.editor import VideoFileClip
import pypandoc
from yoomoney import Quickpay
from yoomoney import Client
import os
import PyPDF2
from config import token, API_TOKEN, card_number

archieve_bot = "https://t.me/ArchieveTool_bot"

client = Client(token)
user = client.account_info()
print("Account number:", user.account)
print("Account balance:", user.balance)
print("Account currency code in ISO 4217 format:", user.currency)
print("Account status:", user.account_status)
print("Account type:", user.account_type)
print("Extended balance information:")
for pair in vars(user.balance_details):
    print("\t-->", pair, ":", vars(user.balance_details).get(pair))
print("Information about linked bank cards:")
cards = user.cards_linked
if len(cards) != 0:
    for card in cards:
        print(card.pan_fragment, " - ", card.type)
else:
    print("No card is linked to the account")
con = sqlite3.connect(
    "lastbdhope.db",
    timeout=5.0,
    detect_types=0,
    isolation_level='DEFERRED',
    check_same_thread=True,
    factory=sqlite3.Connection,
    cached_statements=128,
    uri=False
)

cursor = con.cursor()


# Включаем логирование
logging.basicConfig(level=logging.INFO)
# Создаем экземпляр бота
botuse = Bot(token=API_TOKEN)

# Создаем хранилище состояний
storage = MemoryStorage()

# Создаем экземпляр диспетчера
dp = Dispatcher(storage=storage)

# Начальная клавиатура
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='🗂Архив'),
            KeyboardButton(text='🔄Конвертация')
        ],
        [
            # KeyboardButton(text='✨ChatGPT'),
            KeyboardButton(text='💬Текст в файл')
        ],
        [
            KeyboardButton(text='✅Подписка')
        ]
    ],
    resize_keyboard=True
)

# Клавиатура для конвертирования
conv_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📄Документы в PDF'),
            KeyboardButton(text='📷Изображения')
        ],
        [
            KeyboardButton(text='🔊Аудио'),
            KeyboardButton(text='🎥Видео')
        ],
        [
            KeyboardButton(text='🔙Назад')
        ]
    ],
    resize_keyboard=True
)

subscriptions_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='✨1 день'),
            KeyboardButton(text='⭐️30 дней')
        ],
        [
            KeyboardButton(text='💫1 год')
        ],
        [
            KeyboardButton(text='🔙Назад')
        ]
    ],
    resize_keyboard=True
)
subscriptions_keyboard_oneday = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Подтвердить покупку подписки на 1 день'),
        ],
        [
            KeyboardButton(text='🔙Назад')
        ]

    ],
    resize_keyboard=True
)
subscriptions_keyboard_month = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Подтвердить покупку подписки на 30 дней'),
        ],
        [
            KeyboardButton(text='🔙Назад')
        ]

    ],
    resize_keyboard=True
)
subscriptions_keyboard_year = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Подтвердить покупку подписки на 365 дней'),
        ],
        [
            KeyboardButton(text='🔙Назад')
        ]

    ],
    resize_keyboard=True
)

SUPPORTED_FORMATS = ['JPG', 'JPEG', 'PNG', 'BMP', 'GIF', 'TIFF', 'WEBP']
class ConvertImageClass(StatesGroup):
    waiting_for_image = State()
    waiting_for_format = State()


class ConvertVideoClass(StatesGroup):
    waiting_for_video = State()
    waiting_for_format = State()


class ConvertAudioClass(StatesGroup):
    waiting_for_audio = State()
    waiting_for_format = State()


class ConvertOfficeClass(StatesGroup):
    waiting_for_file = State()
    waiting_for_format = State()


class SubscriptionOne(StatesGroup):
    start_buy = State()
    waiting_for_submit = State()
    waiting_for_buy = State()
    waiting_for_successpay = State()


class SubscriptionMonth(StatesGroup):
    start_buy = State()
    waiting_for_submit = State()
    waiting_for_buy = State()
    waiting_for_successpay = State()


class SubscriptionYear(StatesGroup):
    start_buy = State()
    waiting_for_submit = State()
    waiting_for_buy = State()
    waiting_for_successpay = State()


class TextToFileClass(StatesGroup):
    waiting_for_file_info = State()


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Внимание! Наш бот работает в тестовом режиме, некоторые функции могут быть недоступны. В течение недели мы закончим работу!")
    await message.answer("Привет 👋\nЯ ToolBot,ваш помощник в мире файлов.\nВыберите желаемое действие:",
                         reply_markup=start_keyboard)
    cursor.execute("""
    Select id From Users
    Where name = ?
    """, (message.from_user.id,))
    result = cursor.fetchone()
    current_time  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if result == None:
        cursor.execute("""
        Insert into Users(name, CountAction, LastActionTime)
        Values (?, 0, ?)  
         """, (message.from_user.id, current_time,))
        con.commit()
    else:
        print("Этот бро уже полбзовался нашим ботом")


# Хэндлеры для кнопок
@dp.message(lambda message: message.text in ["🗂Архив", "🔄Конвертация", "✨ChatGPT", "💬Текст в файл", "✅Подписка",
                                             "📄Документы в PDF", "📷Изображения", "🔊Аудио", "🎥Видео", "🔙Назад",
                                             '✨1 день', '⭐️30 дней', '💫1 год', 'Хочу подписку на 1 день',
                                             'Подтвердить покупку подписки на 30 дней',
                                             'Подтвердить покупку подписки на 365 дней', ])
async def handle_button(message: types.Message, state: FSMContext):
    cursor.execute("""
                   SELECT 
                   Users.id, 
                   Users.name,
                   CASE
                       WHEN SubscriptionInformation.sub_id IS NULL THEN 'Нет подписки'
                       WHEN SubscriptionInformation.payed = 0 THEN 'Неоплаченная подписка'
                       WHEN DATETIME(SubscriptionInformation.purchase_date, '+' || SubscriptionInformation.length_days || ' days') >= DATETIME('now') THEN 'Действует активная подписка'
                       ELSE 'Подписка просрочена'
                   END AS subscription_status
                   FROM Users
                   LEFT JOIN SubscriptionInformation 
                       ON Users.sub_id = SubscriptionInformation.sub_id
                   WHERE Users.name = ?;""", (message.from_user.id,))
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
    payment_state = cursor.fetchone()
    if payment_state  != None:
        if payment_state[2] ==  'Подписка просрочена':
            cursor.execute("""UPDATE SubscriptionInformation
                                                                            
                                    Set payed=?, payment_number =?
                                    Where payment_number = ?
                                    """, (
                False, (str(message.from_user.id) + f"oneday{current_datetime}expired"),
                (str(message.from_user.id) + f"oneday{current_datetime}")))
    print(str(message.from_user.first_name) + " " + str(message.from_user.id))
    cursor.execute("""
    SELECT 
        (JULIANDAY('now') - JULIANDAY(LastActionTime)) * 24 AS hours_difference
    FROM users
    WHERE name = ?
    """, (str(message.from_user.id),))

    timebtw = cursor.fetchone()
    print(timebtw)
    if timebtw[0]  >=24:
        await message.answer("Функции бота снова досупны!")
        cursor.execute("""
                                       UPDATE Users
                                       Set CountAction = 0, LastActionTime  =  DATETIME('now')
                                       Where name = ?
                                   """, (message.from_user.id,))
        con.commit()
    if message.text == "🗂Архив":
        cursor.execute("""
                                        SELECT payed 
                                        FROM SubscriptionInformation
                                        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
                                        WHERE Users.name = ?
                                    """, (message.from_user.id,))
        try:
            payment_state = cursor.fetchone()
            print(payment_state)
        except Exception:
            print("Такой записи не существует")
            payment_state = None
        if payment_state == None or payment_state[0] == 0:
            cursor.execute("""
                                    Select CountAction From Users
                                    Where name = ?
                                    """, (message.from_user.id,))
            countact = cursor.fetchone()
            print(countact)
            print(countact[0])
            if countact[0] <= 10:
                await message.reply(f"Для архивации, пожалуйста, воспользуйтесь нашим вторым ботом {archieve_bot}")
            else:
                await message.reply(
                    "У вас закончился лимит работы с ботом, бот для вас снова станет доступен завтра! Если хотите убрать ограничения, можно приобрести подписку")
        else:
            await message.reply(f"Для архивации, пожалуйста, воспользуйтесь нашим вторым ботом {archieve_bot}")


    elif message.text == "🔄Конвертация":
        await message.reply("Выберите тип конвертации", reply_markup=conv_keyboard)
    # elif message.text == "✨ChatGPT":
    #     await message.reply("Coming soon...\n/start")
    elif message.text == "💬Текст в файл":
        await message.reply("Введите запрос по следующему примеру:\nfile.txt\nHello world!")
        await state.set_state(TextToFileClass.waiting_for_file_info)
    elif message.text == "✅Подписка":
        await message.reply("Красава, благодаря тебе мы купим покушать", reply_markup=subscriptions_keyboard)
    elif message.text == "📄Документы в PDF":
        cursor.execute("""
                        SELECT payed 
                        FROM SubscriptionInformation
                        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
                        WHERE Users.name = ?
                    """, (message.from_user.id,))
        try:
            payment_state = cursor.fetchone()
            print(payment_state)
        except Exception:
            print("Такой записи не существует")
            payment_state = None
        if payment_state == None or payment_state[0] == 0:
            cursor.execute("""
                    Select CountAction From Users
                    Where name = ?
                    """, (message.from_user.id,))
            countact = cursor.fetchone()

            if countact[0] <= 10:
                await message.reply("Выберите файл для конвертирования в PDF")
                await state.set_state(ConvertOfficeClass.waiting_for_file)
            else:
                await message.reply(
                    "У вас закончился лимит работы с ботом, бот для вас снова станет доступен завтра! Если хотите убрать ограничения, можно приобрести подписку")
        else:
            await message.reply("Выберите файл для конвертации в PDF")
            await state.set_state(ConvertOfficeClass.waiting_for_file)


    elif message.text == "📷Изображения":
        cursor.execute("""
                                SELECT payed 
                                FROM SubscriptionInformation
                                JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
                                WHERE Users.name = ?
                            """, (message.from_user.id,))
        try:
            payment_state = cursor.fetchone()
            print(payment_state)
        except Exception:
            print("Такой записи не существует")
            payment_state = None
        if payment_state == None or payment_state[0] == 0:
            cursor.execute("""
                            Select CountAction From Users
                            Where name = ?
                            """, (message.from_user.id,))
            countact = cursor.fetchone()

            if countact[0] <= 10:
                cursor.execute("""
                
                """)
                await message.reply("Отправьте, пожалуйста, изображения для конвертирования")
                await state.set_state(ConvertImageClass.waiting_for_image)
            else:
                await message.reply(
                    "У вас закончился лимит работы с ботом, бот для вас снова станет доступен завтра! Если хотите убрать ограничения, можно приобрести подписку")
        else:
            await message.reply("Отправьте, пожалуйста, изображения для конвертирования")
            await state.set_state(ConvertImageClass.waiting_for_image)

    elif message.text == "🔊Аудио":
        cursor.execute("""
                        SELECT payed 
                        FROM SubscriptionInformation
                        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
                        WHERE Users.name = ?
                    """, (message.from_user.id,))
        try:
            payment_state = cursor.fetchone()
            print(payment_state)
        except Exception:
            print("Такой записи не существует")
            payment_state = None
        if payment_state == None or payment_state[0] == 0:
            cursor.execute("""
                    Select CountAction From Users
                    Where name = ?
                    """, (message.from_user.id,))
            countact = cursor.fetchone()
            if countact[0] <= 10:
                await message.reply("Выберите файл для конвертирования аудио")
                await state.set_state(ConvertAudioClass.waiting_for_audio)
            else:
                await message.reply(
                    "У вас закончился лимит работы с ботом, бот для вас снова станет доступен завтра! Если хотите убрать ограничения, можно приобрести подписку")
        else:
            await message.reply("Выберите файл для конвертирования аудио")
            await state.set_state(ConvertAudioClass.waiting_for_audio)
    elif message.text == "🎥Видео":
        cursor.execute("""
                SELECT payed 
                FROM SubscriptionInformation
                JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
                WHERE Users.name = ?
            """, (message.from_user.id,))
        try:
            payment_state = cursor.fetchone()
            print(payment_state)
        except Exception:
            print("Такой записи не существует")
            payment_state = None
        if payment_state == None or payment_state[0] == 0:
            cursor.execute("""
            Select CountAction From Users
            Where name = ?
            """, (message.from_user.id,))
            countact = cursor.fetchone()

            if countact[0] <= 10:
                await message.reply("Выберите файл для конвертирования видео")
                await state.set_state(ConvertVideoClass.waiting_for_video)
            else:
                await message.reply(
                    "У вас закончился лимит работы с ботом, бот для вас снова станет доступен завтра! Если хотите убрать ограничения, можно приобрести подписку")
        else:
            await message.reply("Выберите файл для конвертирования видео")
            await state.set_state(ConvertVideoClass.waiting_for_video)


    elif message.text == "🔙Назад":
        await message.reply("Возврат в главное меню", reply_markup=start_keyboard)
    elif message.text == '✨1 день':
        print(message.from_user.first_name + " хочет купить подписку на 1 день")
        Submit = ["Хочу подписку на 1 день"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.reply(f"Если вы хотите купить подписку на нашего бота, пожалуйста, подтвердите покупку:",
                            reply_markup=keyboard)
        await state.set_state(SubscriptionOne.waiting_for_submit)
    elif message.text == '⭐️30 дней':
        print(message.from_user.first_name + " хочет купить подписку на 30 дней")
        Submit = ["Хочу подписку на 30 дней"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.reply(f"Если вы хотите купить подписку на нашего бота , пожалуйста, подтвердите покупку:",
                            reply_markup=keyboard)
        await state.set_state(SubscriptionMonth.waiting_for_submit)
    elif message.text == '💫1 год':
        print(message.from_user.first_name + " хочет купить подписку на год")
        Submit = ["Хочу подписку на 365 дней"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.reply(f"Если вы хотите купить подписку на нашего бота , пожалуйста, подтвердите покупку:",
                            reply_markup=keyboard)
        await state.set_state(SubscriptionYear.waiting_for_submit)


# подписка на день
@dp.callback_query(StateFilter(SubscriptionOne.waiting_for_submit))
async def want_oneday_sub(callback_query: types.CallbackQuery, state: FSMContext):
    print ("перешел к оплате")
    cursor.execute("""
        SELECT payed 
        FROM SubscriptionInformation
        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
        WHERE Users.name = ?
    """, (callback_query.from_user.id,))  ##проверка, есть ли уже у него такая подписка (оплаченная)
    try:
        payment_state = cursor.fetchone()
        print(payment_state)
    except Exception:
        payment_state = None

    if payment_state == None:  # если такого нет - отправляем ссылку
        # проверка, есть ли в бд такая заявка, но не оплаченная
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")


        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=3,
            label=f"{str(callback_query.from_user.id)}oneday{current_datetime}",
        )
        print(quickpay.label)
        print(callback_query.from_user.id)

        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        usernow = [1, False, 1, current_datetime, str(quickpay.label)]

        cursor.execute("""
             INSERT INTO SubscriptionInformation
             (type_id, payed, length_days, purchase_date, payment_number)
             VALUES (?,?,?,?,?)
         """, usernow)
        # выполняем транзакцию
        con.commit()
        cursor.execute("""
        Select sub_id
        from SubscriptionInformation
        where payment_number = ?""", ((str(quickpay.label)),))
        sub_id = cursor.fetchone()[0]
        print(sub_id)
        # print(sub_id[0])
        subscription = str(sub_id)
        user = [subscription, callback_query.from_user.id, ]
        cursor.execute("""
            Update Users 
            Set sub_id = ?
            Where  name  = ?
        """, user)
        con.commit()
        print(quickpay.base_url)
        Submit = ["Оплатил 1 день подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на 1 день за 49 рублей. \nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 день подписки'",
                                  reply_markup=keyboard)

        await state.set_state(SubscriptionOne.waiting_for_successpay)

    elif payment_state[0] == 0:
        # подписка не оплачена
        cursor.execute("""SELECT payment_number From SubscriptionInformation
                Join Users on Users.sub_id = SubscriptionInformation.sub_id
                Where Users.name = ?""", (callback_query.from_user.id,))
        paynum = cursor.fetchall()
        print(paynum)
        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=3,
            label=f"{paynum[0]}",
        )
        print(quickpay.label)
        print(callback_query.from_user.id)
        Submit = ["Оплатил 1 день подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на 1 день за 49 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 день подписки!'",
                                  reply_markup=keyboard)
        await state.set_state(SubscriptionOne.waiting_for_successpay)
    else:
        cursor.execute("""
                SELECT 
                Users.id, 
                Users.name,
                CASE
                    WHEN SubscriptionInformation.sub_id IS NULL THEN 'Нет подписки'
                    WHEN SubscriptionInformation.payed = 0 THEN 'Неоплаченная подписка'
                    WHEN DATETIME(SubscriptionInformation.purchase_date, '+' || SubscriptionInformation.length_days || ' days') >= DATETIME('now') THEN 'Действует активная подписка'
                    ELSE 'Подписка просрочена'
                END AS subscription_status
                FROM Users
                LEFT JOIN SubscriptionInformation 
                    ON Users.sub_id = SubscriptionInformation.sub_id
                WHERE Users.name = ?;""", (callback_query.from_user.id,))

        payment_state = cursor.fetchone()
        if payment_state != None:
            if payment_state[2] == "Подписка просрочена":
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""UPDATE SubscriptionInformation
                                                                    Set payed=?, payment_number =?
                                                                    Where payment_number = ?
                                                                """, (
                    False, (str(callback_query.from_user.id) + f"oneday{current_datetime}expired"),
                    (str(callback_query.from_user.id) + f"oneday{current_datetime}")))

                # выполняем транзакцию
                con.commit()
                await botuse.send_message(callback_query.from_user.id,
                                          f"Извините, ваша подписка кончилась")
                quickpay = Quickpay(
                    receiver="4100118722189049",
                    quickpay_form="shop",
                    targets="Sponsor this project",
                    paymentType="SB",
                    sum=49,
                    label=f"{callback_query.from_user.id}oneday"
                )
                print(quickpay.label)
                print(callback_query.from_user.id)
                Submit = ["Оплатил 1 день подписки"]
                buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await botuse.send_message(callback_query.from_user.id,
                                          f"Вы собираетесь купить подписку на 1 день за 49 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 день подписки!'",
                                          reply_markup=keyboard)
                await state.set_state(SubscriptionOne.waiting_for_successpay)

            elif payment_state[2] == "Действует активная подписка":
                await botuse.send_message(callback_query.from_user.id,
                                          f"Спасибо, но у вас уже есть оплаченная подписка! \nC любовью, The Coders❤️")

    # await state.set_state(SubscriptionOne.waiting_for_buy)


@dp.callback_query(StateFilter(SubscriptionOne.waiting_for_successpay))
async def check_one_day_payment(callback_query: types.CallbackQuery, state: FSMContext):
    print("Проверка на платеж")
    print(callback_query.from_user.id)
    cursor.execute("""SELECT payment_number From SubscriptionInformation
    Join Users on Users.sub_id = SubscriptionInformation.sub_id
    Where Users.name = ?""", (callback_query.from_user.id,))
    payment = cursor.fetchone()
    client = Client(token)

    history = client.operation_history(label=f"{payment[0]}")
    print(history)
    print("List of operations:")
    print("Next page starts with: ", history.next_record)
    status = None

    for operation in history.operations:
        print()
        print("Operation:", operation.operation_id)
        print("\tStatus     -->", operation.status)
        print("\tDatetime   -->", operation.datetime)
        print("\tTitle      -->", operation.title)
        print("\tPattern id -->", operation.pattern_id)
        print("\tDirection  -->", operation.direction)
        print("\tAmount     -->", operation.amount)
        print("\tLabel      -->", operation.label)
        print("\tType       -->", operation.type)
        if(datetime.datetime.now() - operation.datetime)*24 >= datetime.timedelta(hours=24) :
            if operation.status == "success":
                status = str(operation.status)

    if (status == "success"):
        print("Оплата прошла!")
        # выдаем юзеру подписку
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
        # ОБНОВИТЬ ДАННЫЕ В БД О ПОДПИСКЕ ЮЗЕРА
        cursor.execute("""
                    UPDATE SubscriptionInformation
                    Set payed=?, purchase_date = ?
                    Where payment_number = ?
                """, (True, current_datetime, payment[0],))
        # выполняем транзакцию
        con.commit()
        await botuse.send_message(callback_query.from_user.id,
                                  "Отлично! Вы приобрели подписку! Прятного пользования, \nC любовью, The Coders❤️")
    else:
        print("Не прошла")
        Submit = ["Оплатил 1 день подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id, "Оплата не прошла", reply_markup=keyboard)


# подписка на месяц
@dp.callback_query(StateFilter(SubscriptionMonth.waiting_for_submit))
async def want_oneday_sub(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
        SELECT payed 
        FROM SubscriptionInformation
        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
        WHERE Users.name = ?
    """, (callback_query.from_user.id,))  ##проверка, есть ли уже у него такая подписка (оплаченная)

    try:
        payment_state = cursor.fetchone()

    except Exception:
        print("Такой записи не существует")
        payment_state = None

    if payment_state == None:  # если такого нет - отправляем ссылку
        # проверка, есть ли в бд такая заявка, но не оплаченная
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
        print("пользователя нет в бд или не оформлял заявку")
        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=299,
            label=f"{str(callback_query.from_user.id)}month{current_datetime}"
        )
        print(quickpay.label)
        print(callback_query.from_user.id)
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        usernow = [2, False, 30, current_datetime, str(quickpay.label)]

        cursor.execute("""
             INSERT INTO SubscriptionInformation
             (type_id, payed, length_days, purchase_date, payment_number)
             VALUES (?,?,?,?,?)
         """, usernow)
        # выполняем транзакцию
        con.commit()
        cursor.execute("""
        Select sub_id
        from SubscriptionInformation
        where payment_number = ?""", ((str(quickpay.label)),))
        sub_id = cursor.fetchone()[0]
        print(sub_id)
        # print(sub_id[0])
        subscription = str(sub_id)
        user = [subscription, callback_query.from_user.id, ]
        cursor.execute("""
                    Update Users 
                    Set sub_id = ?
                    Where  name  = ?
                """, user)
        con.commit()
        print(quickpay.base_url)
        Submit = ["Оплатил месяц подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на месяц за 299 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил месяц подписки'",
                                  reply_markup=keyboard)

        await state.set_state(SubscriptionMonth.waiting_for_successpay)


    elif payment_state[0] == 0:
        # подписка не оплачена
        cursor.execute("""SELECT payment_number From SubscriptionInformation
                        Join Users on Users.sub_id = SubscriptionInformation.sub_id
                        Where Users.name = ?""", (callback_query.from_user.id,))
        paynum = cursor.fetchall()
        print(paynum)
        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=299,
            label=f"{paynum[0]}",
        )
        print(quickpay.label)
        print(callback_query.from_user.id)
        Submit = ["Оплатил месяц подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на месяц за 299 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил месяц подписки!'",
                                  reply_markup=keyboard)
        await state.set_state(SubscriptionMonth.waiting_for_successpay)
    else:
        cursor.execute("""
                        SELECT 
                        Users.id, 
                        Users.name,
                        CASE
                            WHEN SubscriptionInformation.sub_id IS NULL THEN 'Нет подписки'
                            WHEN SubscriptionInformation.payed = 0 THEN 'Неоплаченная подписка'
                            WHEN DATETIME(SubscriptionInformation.purchase_date, '+' || SubscriptionInformation.length_days || ' days') >= DATETIME('now') THEN 'Действует активная подписка'
                            ELSE 'Подписка просрочена'
                        END AS subscription_status
                        FROM Users
                        LEFT JOIN SubscriptionInformation 
                            ON Users.sub_id = SubscriptionInformation.sub_id
                        WHERE Users.name = ?;""", (callback_query.from_user.id,))

        payment_state = cursor.fetchone()
        if payment_state != None:
            if payment_state[2] == "Подписка просрочена":
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""UPDATE SubscriptionInformation
                                                                    Set payed=?, payment_number =?
                                                                    Where payment_number = ?
                                                                """, (
                    False, (str(callback_query.from_user.id) + f"month{current_datetime}expired"),
                    (str(callback_query.from_user.id) + f"month{current_datetime}")))

                # выполняем транзакцию
                con.commit()
                await botuse.send_message(callback_query.from_user.id,
                                          f"Извините, ваша подписка кончилась")
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
                quickpay = Quickpay(
                    receiver="4100118722189049",
                    quickpay_form="shop",
                    targets="Sponsor this project",
                    paymentType="SB",
                    sum=299,
                    label=f"{callback_query.from_user.id}month{current_datetime}"
                )
                print(quickpay.label)
                print(callback_query.from_user.id)
                Submit = ["Оплатил месяц подписки"]
                buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await botuse.send_message(callback_query.from_user.id,
                                          f"Вы собираетесь купить подписку на месяц за 299 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 день подписки!'",
                                          reply_markup=keyboard)
                await state.set_state(SubscriptionMonth.waiting_for_successpay)

            elif payment_state[2] == "Действует активная подписка":
                await botuse.send_message(callback_query.from_user.id,
                                          f"Спасибо, но у вас уже есть оплаченная подписка! \nC любовью, The Coders❤️")

    # await state.set_state(SubscriptionOne.waiting_for_buy)


@dp.callback_query(StateFilter(SubscriptionMonth.waiting_for_successpay))
async def check_one_day_payment(callback_query: types.CallbackQuery, state: FSMContext):
    print("Проверка на платеж")
    print(callback_query.from_user.id)
    cursor.execute("""SELECT payment_number From SubscriptionInformation
        Join Users on Users.sub_id = SubscriptionInformation.sub_id
        Where Users.name = ?""", (callback_query.from_user.id,))
    payment = cursor.fetchone()
    client = Client(token)

    history = client.operation_history(label=f"{payment[0]}")
    print(history)
    print("List of operations:")
    print("Next page starts with: ", history.next_record)
    status = None
    for operation in history.operations:
        print()
        print("Operation:", operation.operation_id)
        print("\tStatus     -->", operation.status)
        print("\tDatetime   -->", operation.datetime)
        print("\tTitle      -->", operation.title)
        print("\tPattern id -->", operation.pattern_id)
        print("\tDirection  -->", operation.direction)
        print("\tAmount     -->", operation.amount)
        print("\tLabel      -->", operation.label)
        print("\tType       -->", operation.type)
        if (datetime.datetime.now() - operation.datetime) * 24 >= datetime.timedelta(days=30):
            if operation.status == "success":
                status = str(operation.status)

    if (status == "success"):
        print("Оплата прошла!")
        # выдаем юзеру подписку
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
        # ОБНОВИТЬ ДАННЫЕ В БД О ПОДПИСКЕ ЮЗЕРА
        cursor.execute("""
                        UPDATE SubscriptionInformation
                        Set payed=?, purchase_date = ?
                        Where payment_number = ?
                    """, (True, current_datetime, payment[0],))
        # выполняем транзакцию
        con.commit()
        await botuse.send_message(callback_query.from_user.id,
                                  "Отлично! Вы приобрели подписку! Прятного пользования. \nC любовью, The Coders❤️")
    else:
        print("Не прошла")
        Submit = ["Оплатил месяц подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id, "Оплата не прошла", reply_markup=keyboard)


# подписка на год
@dp.callback_query(StateFilter(SubscriptionYear.waiting_for_submit))
async def want_oneday_sub(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
        SELECT payed 
        FROM SubscriptionInformation
        JOIN Users ON SubscriptionInformation.sub_id = Users.sub_id
        WHERE Users.name = ?
    """, (callback_query.from_user.id,))  ##проверка, есть ли уже у него такая подписка (оплаченная)
    try:
        payment_state = cursor.fetchone()
        print(payment_state)
    except Exception:
        print("Такой записи не существует")
        payment_state = None

    if payment_state == None:  # если такого нет - отправляем ссылку
        # проверка, есть ли в бд такая заявка, но не оплаченная
        print("пользователя нет в бд или не оформлял заявку")
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=799,
            label=f"{str(callback_query.from_user.id)}year{current_datetime}"
        )
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        usernow = [3, False, 365, current_datetime, str(quickpay.label)]

        cursor.execute("""
             INSERT INTO SubscriptionInformation
             (type_id, payed, length_days, purchase_date, payment_number)
             VALUES (?,?,?,?,?)
         """, usernow)
        # выполняем транзакцию
        con.commit()
        cursor.execute("""
        Select sub_id
        from SubscriptionInformation
        where payment_number = ?""", ((str(quickpay.label)),))
        sub_id = cursor.fetchone()[0]
        print(sub_id)
        # print(sub_id[0])
        subscription = str(sub_id)
        user = [subscription, callback_query.from_user.id, ]
        cursor.execute("""
                    Update Users 
                    Set sub_id = ?
                    Where  name  = ?
                """, user)
        con.commit()
        print(quickpay.base_url)
        Submit = ["Оплатил год подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на год за 799 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 год подписки'",
                                  reply_markup=keyboard)

        await state.set_state(SubscriptionYear.waiting_for_successpay)

    elif payment_state[0] == 0:
        cursor.execute("""SELECT payment_number From SubscriptionInformation
                        Join Users on Users.sub_id = SubscriptionInformation.sub_id
                        Where Users.name = ?""", (callback_query.from_user.id,))
        paynum = cursor.fetchall()
        print(paynum)
        quickpay = Quickpay(
            receiver="4100118722189049",
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=799,
            label=f"{paynum[0]}",
        )
        print(quickpay.label)
        print(callback_query.from_user.id)
        Submit = ["Оплатил год подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id,
                                  f"Вы собираетесь купить подписку на год за 799 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n Когда оплатите, нажмите 'Оплатил!'",
                                  reply_markup=keyboard)
        await state.set_state(SubscriptionYear.waiting_for_successpay)
    else:
        cursor.execute("""
                        SELECT 
                        Users.id, 
                        Users.name,
                        CASE
                            WHEN SubscriptionInformation.sub_id IS NULL THEN 'Нет подписки'
                            WHEN SubscriptionInformation.payed = 0 THEN 'Неоплаченная подписка'
                            WHEN DATETIME(SubscriptionInformation.purchase_date, '+' || SubscriptionInformation.length_days || ' days') >= DATETIME('now') THEN 'Действует активная подписка'
                            ELSE 'Подписка просрочена'
                        END AS subscription_status
                        FROM Users
                        LEFT JOIN SubscriptionInformation 
                            ON Users.sub_id = SubscriptionInformation.sub_id
                        WHERE Users.name = ?;""", (callback_query.from_user.id,))

        payment_state = cursor.fetchone()
        if payment_state != None:
            if payment_state[2] == "Подписка просрочена":
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""UPDATE SubscriptionInformation
                                                    Set payed=?, payment_number =?
                                                    Where payment_number = ?
                                                """, (
                False, (str(callback_query.from_user.id) + f"year{current_datetime}expired"),
                (str(callback_query.from_user.id) + f"year{current_datetime}")))

                # выполняем транзакцию
                con.commit()
                await botuse.send_message(callback_query.from_user.id,
                                          f"Извините, ваша подписка кончилась")
                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
                quickpay = Quickpay(
                    receiver="4100118722189049",
                    quickpay_form="shop",
                    targets="Sponsor this project",
                    paymentType="SB",
                    sum=799,
                    label=f"{callback_query.from_user.id}year{current_datetime}"
                )
                print(quickpay.label)
                print(callback_query.from_user.id)
                Submit = ["Оплатил год подписки"]
                buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await botuse.send_message(callback_query.from_user.id,
                                          f"Вы собираетесь купить подписку на год за 799 рублей.\nОплатите счет по ссылке ниже в течение 24 часов.\n {quickpay.base_url} \n После того, как оплатите, нажмите 'Оплатил 1 день подписки!'",
                                          reply_markup=keyboard)
                await state.set_state(SubscriptionYear.waiting_for_successpay)

            elif payment_state[2] == "Действует активная подписка":
                await botuse.send_message(callback_query.from_user.id,
                                          f"Спасибо, но у вас уже есть оплаченная подписка! \nC любовью, The Coders❤️")

    # await state.set_state(SubscriptionOne.waiting_for_buy)


@dp.callback_query(StateFilter(SubscriptionYear.waiting_for_successpay))
async def check_one_day_payment(callback_query: types.CallbackQuery, state: FSMContext):
    print("Проверка на платеж")
    print(callback_query.from_user.id)
    cursor.execute("""SELECT payment_number From SubscriptionInformation
    Join Users on Users.sub_id = SubscriptionInformation.sub_id
    Where Users.name = ?""", (callback_query.from_user.id,))
    payment = cursor.fetchone()
    client = Client(token)
    history = client.operation_history(label=f"{payment[0]}")
    print(history)
    print("List of operations:")
    print("Next page starts with: ", history.next_record)
    status = None
    for operation in history.operations:
        print()
        print("Operation:", operation.operation_id)
        print("\tStatus     -->", operation.status)
        print("\tDatetime   -->", operation.datetime)
        print("\tTitle      -->", operation.title)
        print("\tPattern id -->", operation.pattern_id)
        print("\tDirection  -->", operation.direction)
        print("\tAmount     -->", operation.amount)
        print("\tLabel      -->", operation.label)
        print("\tType       -->", operation.type)
        if (datetime.datetime.now() - operation.datetime) * 24 >= datetime.timedelta(days=365):
            if operation.status == "success":
                status = str(operation.status)
    if (status == "success"):
        print("Оплата прошла!")
        # выдаем юзеру подписку
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")
        # ОБНОВИТЬ ДАННЫЕ В БД О ПОДПИСКЕ ЮЗЕРА
        cursor.execute("""
                    UPDATE SubscriptionInformation
                    Set payed=?, purchase_date = ?
                    Where payment_number = ?
                """, (True, current_datetime, payment[0],))
        # выполняем транзакцию
        con.commit()
        await botuse.send_message(callback_query.from_user.id,
                                  "Отлично! Вы приобрели подписку на целый год! Прятного пользования. \nC любовью, The Coders❤️")
    else:
        Submit = ["Оплатил год подписки"]
        buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in Submit]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await botuse.send_message(callback_query.from_user.id, "Оплата не прошла", reply_markup=keyboard)


@dp.message(StateFilter(TextToFileClass.waiting_for_file_info))
async def handle_text_to_file(message: types.Message, state: FSMContext):
    await TextToFile.handle_text_to_file(message, state)
    await state.clear()


@dp.message(StateFilter(ConvertImageClass.waiting_for_image))
async def handle_image(message: types.Message, state: FSMContext):
    if not message.photo and not message.document:
        await message.reply("Пожалуйста, отправьте изображение.")
        return
    if message.photo:

        file_id = message.photo[-1].file_id
        file = await botuse.get_file(file_id)
        file_path = file.file_path
        mime_type = mimetypes.guess_type(file_path)[0]
        extension = mime_type.split('/')[-1] if mime_type else 'unknown'
    else:
        file_id = message.document.file_id
        file = await botuse.get_file(file_id)
        file_path = file.file_path
        mime_type = mimetypes.guess_type(file_path)[0]
        extension = mime_type.split('/')[-1] if mime_type else 'unknown'
    if extension.upper() not in SUPPORTED_FORMATS:
        await message.reply("Не поддерживаемый формат изображения -" + extension)
        os.remove(file_path)
        return
    await state.update_data(file_id=file_id, extension=extension)

    buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in SUPPORTED_FORMATS]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer(f"Выберите формат для конвертации (исходный формат: {extension}):", reply_markup=keyboard)
    await state.set_state(ConvertImageClass.waiting_for_format)


@dp.callback_query(StateFilter(ConvertImageClass.waiting_for_format))
async def convert_image(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
                               UPDATE Users
                               Set CountAction = CountAction + 1
                               Where name = ?
                           """, (callback_query.from_user.id,))
    con.commit()
    format = callback_query.data.upper()
    data = await state.get_data()
    file_id = data['file_id']

    file = await botuse.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await botuse.download_file(file_path)

    img = PIL.Image.open(downloaded_file)
    output_path = f"converted_image{file_id}.{format.lower()}"
    img.save(output_path, format=format)

    await botuse.send_document(callback_query.from_user.id, FSInputFile(output_path))
    os.remove(output_path)
    await state.clear()


@dp.message(lambda message: message.text == "Конвертировать изображение")
async def start_image_conversion(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, отправьте изображение для конвертации.")
    await state.set_state(ConvertImageClass.waiting_for_image)


# video converting
SUPPORTED_VIDEO_FORMATS = ['MP4', 'AVI', 'MKV', 'WMV']


@dp.message(StateFilter(ConvertVideoClass.waiting_for_video))
async def handle_video(message: types.Message, state: FSMContext):
    if not message.video and not message.document and not message.video_note:
        await message.reply("Пожалуйста, отправьте видеофайл.")
        return
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        file_id = message.video_note.file_id
    file = await botuse.get_file(file_id)
    file_path = file.file_path
    extension = os.path.splitext(file_path)[1][1:].lower()
    if extension.upper() not in SUPPORTED_VIDEO_FORMATS:
        await message.reply(f"Не поддерживаемый формат видеофайла - {extension}")
        os.remove(file_path)
        return
    await state.update_data(file_id=file_id, extension=extension)

    buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in SUPPORTED_VIDEO_FORMATS]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer(f"Выберите формат для конвертации (исходный формат: {extension}):", reply_markup=keyboard)
    await state.set_state(ConvertVideoClass.waiting_for_format)


@dp.callback_query(StateFilter(ConvertVideoClass.waiting_for_format))
async def convert_video(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
                           UPDATE Users
                           Set CountAction = CountAction + 1
                           Where name = ?
                       """, (callback_query.from_user.id,))
    con.commit()
    format = callback_query.data.upper()
    data = await state.get_data()
    file_id = data['file_id']

    file = await botuse.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await botuse.download_file(file_path)

    # Сохраняем BytesIO во временный файл
    tmp_file_path = f"tmp_video_file{file_id}." + data['extension']
    with open(tmp_file_path, "wb") as tmp_file:
        tmp_file.write(downloaded_file.getbuffer())

    # Конвертация видео с использованием moviepy
    video_clip = VideoFileClip(tmp_file_path)
    output_path = f"converted_video{file_id}.{format.lower()}"

    if format.lower() == "mp4":
        video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    elif format.lower() == "mkv" or format.lower() == "wmv" or format.lower() == "avi":
        video_clip.write_videofile(output_path, codec="libvpx", audio_codec="aac")
    else:
        video_clip.write_videofile(output_path, codec=f"{format.lower()}")

    await botuse.send_document(callback_query.from_user.id, FSInputFile(output_path))
    os.remove(output_path)
    os.remove(tmp_file_path)  # Удаляем временный файл
    await state.clear()


# аудио
SUPPORTED_AUDIO_FORMATS = ['MP3', 'WAV', 'OGG', 'FLAC', 'AAC', 'OGA']
@dp.message(StateFilter(ConvertAudioClass.waiting_for_audio))
async def handle_audio(message: types.Message, state: FSMContext):
    if not message.audio and not message.voice and not message.document:
        await message.reply("Пожалуйста, отправьте аудиофайл.")
        return
    if message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    else:
        file_id = message.document.file_id
    file = await botuse.get_file(file_id)
    file_path = file.file_path
    extension = os.path.splitext(file_path)[1][1:].lower()
    if extension.upper() not in SUPPORTED_AUDIO_FORMATS:
        await message.reply("Не поддерживаемый формат аудио - " + extension.lower())
        os.remove(file_path)
        return
    await state.update_data(file_id=file_id, extension=extension)

    buttons = [InlineKeyboardButton(text=fmt, callback_data=fmt.lower()) for fmt in SUPPORTED_AUDIO_FORMATS]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer(f"Выберите формат для конвертации (исходный формат: {extension}):", reply_markup=keyboard)
    await state.set_state(ConvertAudioClass.waiting_for_format)


@dp.callback_query(StateFilter(ConvertAudioClass.waiting_for_format))
async def convert_audio(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
                              UPDATE Users
                              Set CountAction = CountAction + 1
                              Where name = ?
                          """, (callback_query.from_user.id,))
    con.commit()
    format = callback_query.data.upper()
    data = await state.get_data()
    file_id = data['file_id']

    file = await botuse.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await botuse.download_file(file_path)

    # Сохраняем BytesIO во временный файл
    tmp_file_path = f"tmp_audio_file{file_id}." + data['extension']
    with open(tmp_file_path, "wb") as tmp_file:
        tmp_file.write(downloaded_file.getbuffer())
    # Конвертация аудио с использованием pydub
    audio = AudioSegment.from_file(tmp_file_path)
    output_path = f"converted_audio{file_id}.{format.lower()}"
    audio.export(output_path, format=format.lower())

    await callback_query.answer()
    if format.lower()  == "oga":
        await botuse.send_audio(callback_query.from_user.id, FSInputFile(output_path))
    else:
        await botuse.send_document(callback_query.from_user.id, FSInputFile(output_path))
    os.remove(output_path)
    os.remove(tmp_file_path)  # Удаляем временный файл
    await state.clear()


@dp.message(lambda message: message.text == "Конвертировать аудио")
async def start_audio_conversion(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, отправьте аудиофайл для конвертации.")
    await state.set_state(ConvertAudioClass.waiting_for_audio)


@dp.message(lambda message: message.text == "Конвертировать видео")
async def start_video_conversion(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, отправьте видео для конвертации.")
    await state.set_state(ConvertVideoClass.waiting_for_video)


# конв в пдф
SUPPORTED_OFFICE_FORMATS = ['DOCX']


@dp.message(StateFilter(ConvertOfficeClass.waiting_for_file))
async def handle_office_file(message: types.Message, state: FSMContext):
    if not message.document:
        await message.reply("Пожалуйста, отправьте файл DOCX, PPTX или XLS.")
        return

    file_id = message.document.file_id
    file = await botuse.get_file(file_id)
    file_path = file.file_path
    extension = os.path.splitext(file_path)[1][1:].upper()

    if extension not in SUPPORTED_OFFICE_FORMATS:
        await message.reply(
            f"Неподдерживаемый формат файла. Поддерживаемые форматы: {', '.join(SUPPORTED_OFFICE_FORMATS)}")
        os.remove(file_path)
        return

    await state.update_data(file_id=file_id, extension=extension)
    await state.set_state(ConvertOfficeClass.waiting_for_format)

    buttons = [InlineKeyboardButton(text="PDF", callback_data="pdf")]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.reply("Выберите формат для конвертации (PDF)", reply_markup=keyboard)


@dp.callback_query(StateFilter(ConvertOfficeClass.waiting_for_format))
async def convert_office_file(callback_query: types.CallbackQuery, state: FSMContext):
    cursor.execute("""
                              UPDATE Users
                              Set CountAction = CountAction + 1
                              Where name = ?
                          """, (callback_query.from_user.id,))
    con.commit()
    data = await state.get_data()
    file_id = data['file_id']
    extension = data['extension']

    file = await botuse.get_file(file_id)
    file_path = file.file_path
    downloaded_file = await botuse.download_file(file_path)

    # Сохраняем BytesIO во временный файл
    tmp_file_path = f"tmp_office_file{file_id}.{extension.lower()}"
    with open(tmp_file_path, "wb") as tmp_file:
        tmp_file.write(downloaded_file.getbuffer())

    # Конвертация в PDF
    output_path = f"converted_file{file_id}.pdf"
    f = open(output_path, "a+")
    f.close()
    # if extension.upper() == "PPTX":
    #     presentation = pptx.Presentation(tmp_file_path)
    #     presentation.save(output_path, pptx.util.PresentationWriter().write)
    if extension.upper() == "DOCX":

        pypandoc.convert_file(tmp_file_path, 'pdf', outputfile=output_path)

    elif extension.upper() == "PPTX":
        # List To Delete All The Individual ".pdf" Files
        EOF_MARKER = b'%%EOF'
        dellst = []
        with open(tmp_file_path,  "rb") as f:
            contents  =  f.read()
        if EOF_MARKER in contents:
            contents  =  contents.replace(EOF_MARKER, b'')
            contents  =  contents + EOF_MARKER
        else:
            # Some files really don't have an EOF marker
            # In this case it helped to manually review the end of the file
            print(contents[-8:])  # see last characters at the end of the file
            # printed b'\n%%EO%E'
            contents = contents[:-6] + EOF_MARKER

        with open(tmp_file_path, 'wb') as f:
            f.write(contents)
        merger = PyPDF2.PdfFileMerger()
        # Loop To Gather All ".pdf" Files In The inputflder
        merger.append(tmp_file_path)
        dellst.append(tmp_file_path)
        dellst.append(contents)
        # Will Merge All The PDFs
        merger.write(f"{output_path}.pdf")
        merger.close()
        # Will Delete The Individual PDFs
        for file in dellst:
            os.remove(file)
    elif extension.upper() == "XLSX":
        pypandoc.convert(tmp_file_path, output_path)
    await state.clear()
    await callback_query.answer()  # Подтверждаем получение callback_query
    await botuse.send_document(callback_query.from_user.id, FSInputFile(output_path))
    os.remove(output_path)
    os.remove(tmp_file_path)  # Удаляем временный файл
    await state.clear()


@dp.message(lambda message: message.text == "Конвертировать офисный файл")
async def start_office_conversion(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, отправьте файл DOCX или PPTX для конвертации.")
    await state.set_state(ConvertOfficeClass.waiting_for_file)


async def main():
    await dp.start_polling(botuse)


if __name__ == "__main__":
    asyncio.run(main())

# async def handle_text_to_file(message: types.Message, state: FSMContext):
#     try:
#         # Разделяем сообщение на имя файла и текст
#         file_info = message.text.split('\n', 1)
#         if len(file_info) != 2:
#             await message.reply("Некорректный формат. Введите запрос по следующему примеру:\nfile.txt\nHello world!")
#             await state.set_state(TextToFileClass.waiting_for_file_info)
#             return
#         file_name, file_content = file_info
#
#         # Получаем расширение файла из имени
#         file_extension = os.path.splitext(file_name)[1].lower()
#
#         # Проверяем корректность имени файла
#         if not file_name or not file_content:
#             await message.reply("Некорректный формат. Введите запрос по следующему примеру:\nfile.txt\nHello world!")
#             await state.set_state(TextToFileClass.waiting_for_file_info)
#             await state.clear()
#             return
#
#         # Создаем файл
#         if file_extension == ".docx":
#             # Создаем и записываем DOCX файл
#             doc = Document()
#             doc.add_paragraph(file_content)
#             file_path = file_name  # Используем имя файла без дублирования расширения
#             doc.save(file_path)
#             await message.reply(f"Файл '{file_name}' успешно создан и заполнен текстом.")
#             docx_file = FSInputFile(file_path)
#             await message.answer_document(docx_file)
#
#         else:
#             # Создаем текстовый файл
#             file_path = file_name  # Используем имя файла без дублирования расширения
#             with open(file_path, "w", encoding="utf-8") as file:
#                 file.write(file_content)
#             await message.reply(f"Файл '{file_name}' успешно создан и заполнен текстом.")
#             text_file = FSInputFile(file_path)
#             await message.answer_document(text_file)
#
#         # Удаляем файл после отправки
#         os.remove(file_path)
#
#     except Exception as e:
#         await message.reply("Произошла ошибка при создании файла.")
#         logging.error(f"Ошибка при создании файла: {e}")

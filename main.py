import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message 
from aiogram.filters import CommandStart
from check.get_address import AddressValidator
from check.get_apartment import apartment_validity
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from settings import settings

from db.query import *
from db.models import *

TOKEN = settings.bots.bot_token

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()

class HandleAddress(StatesGroup):
    handling_address = State()
    handling_apartment = State()
    delete_apartment = State()


def get_inline_keyboard_handle_address():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Внести в черный список', callback_data="add_to_black_list")
    keyboard_builder.button(text='Проверить в черном списке', callback_data="check_address_in_black_list")
    keyboard_builder.button(text='Изменить адрес', callback_data="change_address")
    keyboard_builder.adjust(2,1)
    return keyboard_builder.as_markup()

def get_inline_keyboard_add_apartment():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Добавить квартиру', callback_data="add_apartment")
    keyboard_builder.button(text='Дом без квартир', callback_data="is_villa")
    keyboard_builder.button(text='Вернуться в начало', callback_data="go_to_start")
    keyboard_builder.adjust(2,1)
    return keyboard_builder.as_markup()

def get_inline_keyboard_delete_address():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Удалить адрес', callback_data="delete_address")
    keyboard_builder.button(text='Вернуться в начало', callback_data="go_to_start")
    keyboard_builder.adjust(2,1)
    return keyboard_builder.as_markup()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await add_user_if_not_exists(message.from_user.id) 
    await message.answer(f"Привет, {message.from_user.full_name}, пришли адрес для проверки.")
    await state.set_state(HandleAddress.handling_address)

@dp.callback_query(lambda c: c.data == "go_to_start")
async def go_to_start(callback_query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Привет, {callback_query.from_user.full_name}, пришли адрес для проверки.")
    await state.set_state(HandleAddress.handling_address)

#Удаление адреса
@dp.callback_query(lambda c: c.data == "delete_address", HandleAddress.handling_apartment)
async def delete_address(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    address = data.get('validated_address')
    apartment = data.get('apartment_number')
    await bot.answer_callback_query(callback_query.id)
    try:
        await delete_apartment(text=address, apartment_num=apartment)
        await bot.send_message(
            callback_query.from_user.id, 
            f"Удален адрес: <b>{address} {apartment}</b>"
        )
    except:
        await bot.send_message(
            callback_query.from_user.id, 
            f"Произошла ошибка."
        )
    finally:
        await state.clear()
        await bot.send_message(callback_query.from_user.id, "Нажмите /start для нового запроса.")

# Валидация адреса
@dp.message(F.text, HandleAddress.handling_address)
async def return_validated_address(message: Message, state: FSMContext):
    address = AddressValidator()
    validated_address = await address.validate_address(message.text)
    await state.update_data(validated_address=validated_address)
    validation_granularity = await address.get_validation_granularity(validated_address)
    if validation_granularity.lower() == "other":
        await message.answer(
            f"Похоже, ты прислал невалидный адрес <b>{message.text}</b>, я не могу его найти на гугл-картах. Попробуй еще раз найти этот адрес на гугл-картах и скопировать его оттуда.")
    else:
        await message.answer(
            f"Отлично, {message.from_user.full_name}, ты прислал адрес <b>{message.text}</b>.\n" \
            f"В гугл-картах нашелся этот адрес нашелся как <b>{validated_address}</b>.\n" \
            f"Что ты хочешь сделать?", 
            reply_markup=get_inline_keyboard_handle_address()
        )

# Внести адрес в черный список
@dp.callback_query(lambda c: c.data == "add_to_black_list", HandleAddress.handling_address)
async def add_address_button(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, 
        f"Выберите, что вы хотите сделать с адресом <b>{data.get('validated_address')}</b>.",
        reply_markup=get_inline_keyboard_add_apartment()
    )
    await state.set_state(HandleAddress.handling_apartment) 


# Проверка адреса на наличие в черном списке
@dp.callback_query(lambda c: c.data == "check_address_in_black_list", HandleAddress.handling_address)
async def check_address_button(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    address = data.get('validated_address')
    await bot.answer_callback_query(callback_query.id)
    if await address_exists(address):
        await bot.send_message(
            callback_query.from_user.id, 
            f"Найдены следующие адреса в черном списке:\n{await get_address_and_all_apartments(address)}"
        )
    else:
        await bot.send_message(
            callback_query.from_user.id, 
            f"Адреса <b>{address}</b> не найдено в черном списке."
        )
    await state.clear()
    await bot.send_message(callback_query.from_user.id, "Нажмите /start для нового запроса.")


# Изменить ранее введенный адрес
@dp.callback_query(lambda c: c.data == "change_address", HandleAddress.handling_address)
async def reply_for_another_address(callback_query: CallbackQuery):
    await callback_query.answer()  # Отправляем пустое callback_query ответ, чтобы закрыть всплывающее уведомление
    await bot.send_message(
        callback_query.from_user.id,
        f"Хорошо, {callback_query.from_user.full_name}, пришли другой адрес и выбери потом, что ты хочешь с ним сделать."
    )

# Неизвестная команда
@dp.callback_query(HandleAddress.handling_address)
async def reply_for_another_address(callback_query: CallbackQuery):
    await callback_query.answer()  # Отправляем пустое callback_query ответ, чтобы закрыть всплывающее уведомление
    await bot.send_message(
        callback_query.from_user.id,
        f"Извини, {callback_query.from_user.full_name}, я не знаю, как обработать эту команду, попробуй еще раз.",
        reply_markup=get_inline_keyboard_add_apartment()
    )

# Вводим номер апартаментов
@dp.callback_query(lambda c: c.data == "add_apartment")
async def add_apartment_number(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Отправляем пустое callback_query ответ, чтобы закрыть всплывающее уведомление
    await bot.send_message(
        callback_query.from_user.id,
        f"Хорошо, {callback_query.from_user.full_name}, пришли номер апартаментов."
    )
    state.get_state(HandleAddress.handling_apartment)

# Добавление квартиры по конкретному адресу в черный список
@dp.message(F.text, HandleAddress.handling_apartment)
async def add_apartment_button(message: Message, state: FSMContext):
    if apartment_validity(message.text):
        data = await state.get_data()
        await add_address(data.get('validated_address'), message.from_user.id)
        id_address = await get_address_id(data.get('validated_address'))
        await add_apartment_to_address(apartment_num=message.text, address_id=id_address)
        await message.answer(
        f"Отлично, {message.from_user.full_name}, твоя квартира {message.text.upper()} добавлена для адреса {data.get('validated_address')}",
        reply_markup=get_inline_keyboard_delete_address()
        )
        await state.update_data(apartment_number=message.text.upper())
    else:
        await message.answer(
        f"Извини, {message.from_user.full_name}, похоже, ты прислал неправильный номер апартаментов. В Аргентине номера апартаментов указываются так: сначала номер этажа, потом номер апартаментов (только латинские буквы).",
        reply_markup=get_inline_keyboard_add_apartment()
        )

# Добавление дома целиком (нет квартир)
@dp.callback_query(lambda c: c.data == "is_villa")
async def add_apartment_number(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Отправляем пустое callback_query ответ, чтобы закрыть всплывающее уведомление
    data = await state.get_data()
    validated_address = data.get('validated_address')
    await add_address(validated_address, callback_query.from_user.id)
    id_address = await get_address_id(validated_address)
    await set_no_apartments(address_id=id_address)
    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        f"Отлично, {callback_query.from_user.full_name}, адрес {validated_address} добавлен целиком.",
        reply_markup=get_inline_keyboard_delete_address()
    )
    await state.clear()

async def create_tables():
    async with async_engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

async def main():
    await create_tables()
    logging.basicConfig(filename='bot.log', level=logging.INFO,
                        format="%(asctime)s - [%(levelname)s] - %(name)s - "
                        "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
                        )
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

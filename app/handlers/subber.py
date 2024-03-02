from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.create_bot import dp, bot
from app.logs import logging
from app.states import Profile
from app.utils.parser import fetch_and_parse_data, send_collab_request


@dp.message_handler(commands=['start', 'restart'])
async def start_cmd(message: types.Message):

    await Profile.get_token.set()
    await message.answer(f" Welcome to the *Subber Requester* by ARNI Concepts! \n\n",
                         parse_mode=types.ParseMode.MARKDOWN)

    await bot.send_photo(chat_id=message.chat.id, photo=open('app/data/token.png', 'rb'),
                         caption="Send me your token from the 'Cookies' section ⬇️")


@dp.message_handler(state=Profile.get_token)
async def get_token(message: types, state: FSMContext):
    token = message.text
    await bot.delete_message(message.chat.id, message.message_id)
    user_data = await fetch_and_parse_data(token)

    if "error" not in user_data:
        username = user_data.get("username", "Unknown")  # Default to 'Unknown' if username is not found
        dao_titles = [role["community"]["title"] for role in user_data.get("community_roles", [])]

        response_message = (f"👤 *{username}* \n\n"
                            f"🗂 DAOs: _{', '.join(dao_titles) if dao_titles else 'None'}_")
        await message.answer(response_message, parse_mode=types.ParseMode.MARKDOWN)
        await state.update_data(user_data=user_data, token=token)

        await bot.send_photo(chat_id=message.chat.id, photo=open('app/data/links.png', 'rb'),
                             caption="Send me links in format (max. 20): ")
        await Profile.send_req.set()
    else:
        await message.answer(f"❌ The token appears to be invalid. Please try again.\n\n"
                             f"Error: {user_data['error']}")


@dp.message_handler(state=Profile.send_req)
async def send_requests(message: types, state: FSMContext):
    try:
        urls = message.text.split()  # Предполагаем, что URLs разделены пробелами или новыми строками.
        data = await state.get_data()
        token = data.get("token")
        user_data = data.get("user_data")

        wait_mess = await bot.send_message(message.from_user.id, "_Starting script ..._", parse_mode=types.ParseMode.MARKDOWN)


        results = []  # Список для сохранения результатов для каждой ссылки

        for index, url in enumerate(urls, start=1):
            response = await send_collab_request(token, url, user_data)
            if "error" not in response:
                result_message = f"URL-{index} - _Success_ 🟢"
            else:
                result_message = f"URL-{index} - _Failed_ 🔴"

            await bot.edit_message_text(f"READY - {index} / {len(urls)} ", chat_id=message.chat.id, message_id=wait_mess.message_id,
                                        parse_mode=types.ParseMode.HTML)
            results.append(result_message)

        await bot.delete_message(message.chat.id, wait_mess.message_id)

        final_report = "\n".join(results)
        await message.answer(f" *Finished processing URLs* \n\n{final_report}", parse_mode=types.ParseMode.MARKDOWN)
        await bot.send_photo(chat_id=message.chat.id, photo=open('app/data/links.png', 'rb'),
                             caption="Send me links in format (max. 20): ")
        await Profile.send_req.set()

    except Exception as err_:
        logging.error(f"f{err_}")
        await message.answer(f"🔴 ERROR 🔴 \n\n{err_} \n\n"
                             f"Send to support")
        await Profile.send_req.set()

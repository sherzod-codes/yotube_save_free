import logging
import requests
from urllib.request import urlretrieve
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import MediaGroup, InputFile
import re

logging.basicConfig(level=logging.INFO)

bot = Bot('7981487885:AAGKG3zN6zwonfzuJRwkQ16PeYbC8aL4jp0')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserState(StatesGroup):
    save = State()


def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+'
    return re.match(youtube_regex, url) is not None


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer('Assalomu alaykum, YouTube-dan video va qo\'shig\'ini yuklab olishni boshlaymiz.')
    await UserState.save.set()
    await message.answer("Video URL-ni kiriting:")


@dp.message_handler(state=UserState.save)
async def get_video(message: types.Message, state: FSMContext):
    user_url = message.text

    if not is_valid_youtube_url(user_url):
        await message.answer('Iltimos, haqiqiy YouTube URL kiriting.')
        return

    async with state.proxy() as data:
        data['save'] = user_url

    await state.finish()

    # Make API request to download video and audio
    url = "https://youtube-quick-video-downloader.p.rapidapi.com/api/youtube/links"
    payload = {"url": user_url}
    headers = {
        "x-rapidapi-key": "0b765b51b6msh59006515055e2b2p1e1facjsnfa954e780c20",
        "x-rapidapi-host": "youtube-quick-video-downloader.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'urls' in data[0]:
            video_url = data[0]['urls'][0]['url']
            title = data[0]['meta']['title']
            video_path = f"{title}.mp4"

            try:
                # Download video
                urlretrieve(video_url, video_path)
                await message.answer(f"Video '{title}' muvaffaqiyatli yuklandi!")

                # Prepare media group and send video
                media = MediaGroup()
                media.attach_video(InputFile(video_path))

                # Send the media group
                await message.answer_media_group(media)

                # Clean up the file after sending
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception as e:
                await message.answer(f'Yuklab olishda xatolik yuz berdi: {str(e)}')
        else:
            await message.answer('API javobi noto\'g\'ri: URL topilmadi.')
    else:
        await message.answer('Yuklab olishda xatolik yuz berdi. Iltimos, URL-ni tekshiring.')


@dp.message_handler(commands=['card'])
async def send_card(message: types.Message):
    await message.answer("Sizning vizit kartangiz tayyor. Yuklab olish uchun yuqoridagi URLni kiriting.")


@dp.message_handler(commands=['cancel'], state=UserState.save)
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Yuklab olish jarayoni bekor qilindi.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

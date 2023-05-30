import asyncio
import os
from datetime import datetime, timedelta, date

import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktime.settings")
django.setup()

from aiogram import Bot, Dispatcher, types, executor
from telega.models import Worker, Schedule

bot = Bot(token="")

dp = Dispatcher(bot)

MANAGER_CHAT_ID = "6130285347"


current_time = datetime.now().time().strftime("%H:%M")
current_day = datetime.today().weekday()


def calculate_time_difference(start_time, time_now):
    current = datetime.strptime(time_now, '%H:%M').time()
    difference = timedelta(hours=current.hour,
                           minutes=current.minute) - timedelta(
        hours=start_time.hour, minutes=start_time.minute)
    hours = difference.seconds // 3600
    minutes = (difference.seconds % 3600) // 60
    return timedelta(hours=hours, minutes=minutes)


async def send_access_denied_message(message: types.Message):
    await message.answer(
        "Доступ запрещен! Тебя нет в нашей базе данных. Напиши админу для "
        "регистрации."
    )


@sync_to_async
def get_worker_by_nickname(username):
    return Worker.objects.filter(username=username).first()


@sync_to_async
def get_all_workers(status=None):
    if status == 'active':
        workers = Worker.objects.filter(active=True)
    elif status == 'inactive':
        workers = Worker.objects.filter(active=False)
    else:
        workers = Worker.objects.all()
    names = [worker.name for worker in workers]
    names_str = '\n'.join(names)
    return names_str


@sync_to_async
def make_worker_active(worker):
    worker.active = True
    worker.save()
    return worker


@sync_to_async
def make_worker_inactive(worker):
    worker.active = False
    worker.save()
    return worker


@sync_to_async
def get_schedule(worker):
    return Schedule.objects.filter(worker=worker, date=date.today()).first()


@sync_to_async
def create_new_day(worker, start_time):
    return Schedule.objects.create(worker=worker, start_time=start_time)


async def send_work_start_notification(worker):
    if current_time >= worker.work_start_time and \
            not current_day != worker.rest_day:
        await bot.send_message(
            worker.chat_id, f"Хэллоу, {worker.name}! У тебя смена $$$")
    else:
        await bot.send_message(
            worker.chat_id, f"Хэллоу, {worker.name}! Хорошего выходного <3")


async def send_manager_notification(worker):
    await bot.send_message(MANAGER_CHAT_ID, f"{worker.name} не реагирует!")


async def schedule_notifications():
    CHECK_INTERVAL_SECONDS = 300
    NOTIFICATION_ATTEMPTS = 5
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        workers = await sync_to_async(Worker.objects.all)()
        for worker in workers:
            if not worker.active:
                await send_work_start_notification(worker)
                NOTIFICATION_ATTEMPTS -= 1
                if not NOTIFICATION_ATTEMPTS:
                    await send_manager_notification(worker)
                    await bot.send_message(
                        worker.chat_id,
                        f"Ты не на смене, {worker.name}! У тебя все еще есть "
                        f"возможность отправить /in в чат и выйти на смену. "
                        f"Но оповещение направленр менеджерам.")


@dp.message_handler(commands=["start"])
async def set_work_start(message: types.Message):
    username = message.chat.username
    worker = await get_worker_by_nickname(username)
    if worker:
        await message.answer(
            f"Привет {worker.name}! Ты найден в нашей базе данных. Твоя "
            f"смена начинается в {worker.work_start_time.strftime('%H:%M')}."
        )
    else:
        await send_access_denied_message()


@dp.message_handler(commands=["in"])
async def check_in(message: types.Message):
    global starting_time
    starting_time = current_time
    username = message.chat.username
    worker = await get_worker_by_nickname(username)
    if worker:
        schedule = await get_schedule(worker)
        if schedule:
            await message.answer(f"Ты уже чекинился в {starting_time}")
        else:
            await create_new_day(worker=worker, start_time=starting_time)
            await make_worker_active(worker)
            await message.answer(
                f"Ты начал в {starting_time}. Успешной работы!"
            )
    else:
        await send_access_denied_message()


@dp.message_handler(commands=["period"])
async def check_period(message: types.Message):
    await process_check_time(message, is_checkout=False)


@dp.message_handler(commands=["out"])
async def check_out(message: types.Message):
    await process_check_time(message, is_checkout=True)


async def process_check_time(message: types.Message, is_checkout: bool):
    username = message.chat.username
    worker = await get_worker_by_nickname(username)
    schedule = None
    try:
        schedule = await get_schedule(worker)
        schedule.period_time = calculate_time_difference(
            schedule.start_time, current_time
        )
    except AttributeError:
        await message.answer("Ты не открыл сегодня смену.")
    if worker:
        if is_checkout:
            schedule.end_time = current_time
            await sync_to_async(schedule.save)()
            await make_worker_inactive(worker)
            await message.answer(
                            f"Смена закрыта в {schedule.end_time}."
                            f"Вы отработали {schedule.period_time}ч."
                        )
        else:
            await message.answer(
                f"Вы отработали {schedule.period_time}ч."
            )
    else:
        await send_access_denied_message()


@dp.message_handler(commands=["workers"])
async def get_active_workers(message: types.Message):
    if len(message.get_args().split()) > 0:
        command = message.get_args().split()[0]
        if command == 'active':
            names = await get_all_workers('active')
        elif command == 'inactive':
            names = await get_all_workers('inactive')
    else:
        names = await get_all_workers()
    await bot.send_message(message.chat.id, f"Workers:\n{names}")


async def on_startup(_):
    print("Bot started.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

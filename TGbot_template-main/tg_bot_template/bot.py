import asyncio
from typing import Any

import aioschedule
from aiogram import types, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from loguru import logger

from . import dp
from .bot_content import features
from .bot_content.errors import Errors
from .bot_infra.callbacks import game_cb
from .bot_infra.filters import CreatorFilter, NonRegistrationFilter, RegistrationFilter
from .bot_infra.states import UserForm, UserFormData
from .bot_lib.aiogram_overloads import DbDispatcher
from .bot_lib.bot_feature import Feature, InlineButton, TgUser
from .bot_lib.utils import bot_edit_callback_message, bot_safe_send_message, bot_safe_send_photo
from .config import settings
from .db_infra import db
from .db_infra.db import check_user_registered

# Создаем роутер для хендлеров
router = Router()

# filters binding - в aiogram 3.x фильтры работают по-другому
# dp.filters_factory.bind(CreatorFilter)
# dp.filters_factory.bind(RegistrationFilter)
# dp.filters_factory.bind(NonRegistrationFilter)


# -------------------------------------------- BASE HANDLERS ----------------------------------------------------------
@router.message(lambda message: features.ping_ftr.find_triggers(message))
async def ping(msg: Message) -> None:
    await bot_safe_send_message(dp, msg.from_user.id, features.ping_ftr.text)  # type: ignore[arg-type]


@router.message(lambda message: features.creator_ftr.find_triggers(message))
async def creator_filter_check(msg: Message) -> None:
    # Проверяем creator фильтр вручную
    if settings.creator_id is None or msg.from_user.id == settings.creator_id:
        await msg.answer(features.creator_ftr.text, parse_mode=ParseMode.MARKDOWN)


@router.message(F.text.in_(features.cancel_ftr.triggers))
async def cancel_command(msg: Message, state: FSMContext) -> None:
    await msg.answer(features.cancel_ftr.text)
    if await state.get_state() is not None:
        await state.clear()
    await main_menu(from_user_id=msg.from_user.id)


@router.callback_query(lambda c: c.data in features.cancel_ftr.triggers)
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await bot_edit_callback_message(dp, callback, features.cancel_ftr.text)
    if await state.get_state() is not None:
        await state.clear()
    await main_menu(from_user_id=callback.from_user.id)


@router.callback_query(game_cb.filter(action=features.start_ftr.callback_action))
@router.message(F.text.in_(features.start_ftr.triggers))
async def start(msg: Message | CallbackQuery) -> None:
    # Проверяем регистрацию вручную
    is_registered = await check_user_registered(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
    if not is_registered:
        return
    
    await main_menu(from_user_id=msg.from_user.id)
    if isinstance(msg, CallbackQuery):
        await msg.answer()


@router.message(F.text.in_(features.help_ftr.triggers))
async def help_feature(msg: Message) -> None:
    # Проверяем регистрацию вручную
    is_registered = await check_user_registered(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
    if not is_registered:
        return
    
    await msg.answer(features.help_ftr.text, reply_markup=features.empty.kb)


async def main_menu(*, from_user_id: int) -> None:
    text = f"{features.start_ftr.text}\n\n{features.start_ftr.menu.text}"  # type: ignore[union-attr]
    await bot_safe_send_message(dp, from_user_id, text, reply_markup=features.start_ftr.kb)


# -------------------------------------------- PROFILE HANDLERS -------------------------------------------------------
@router.message(F.text.in_(features.set_user_info.triggers))
async def set_name(msg: Message, state: FSMContext) -> None:
    # Проверяем регистрацию вручную
    is_registered = await check_user_registered(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
    if not is_registered:
        return
    
    await msg.answer(features.set_user_info.text, reply_markup=features.cancel_ftr.kb)
    await state.set_state(UserForm.name)


@router.message(F.text | F.caption, UserForm.name)
async def add_form_name(msg: Message, state: FSMContext) -> None:
    await fill_form(msg=msg, feature=features.set_user_name, form=UserForm, state=state)


@router.message(F.text | F.caption, UserForm.info)
async def add_form_info(msg: Message, state: FSMContext) -> None:
    await fill_form(msg=msg, feature=features.set_user_about, form=UserForm, state=state)


async def fill_form(*, msg: Message, feature: Feature, form: type[StatesGroup], state: FSMContext) -> None:
    await state.update_data(**{feature.data_key: msg.caption or msg.text})
    await form.next()
    await msg.answer(feature.text, reply_markup=features.cancel_ftr.kb)


@router.message(F.photo, UserForm.photo)
async def add_form_photo(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_form_data = UserFormData(
        name=data[features.set_user_name.data_key],
        info=data[features.set_user_about.data_key],
        photo=msg.photo[-1].file_id,
    )
    tg_user = TgUser(tg_id=msg.from_user.id, username=msg.from_user.username)
    await db.update_user_info(tg_user=tg_user, user_form_data=user_form_data)
    await state.clear()
    await msg.answer(features.set_user_info.text2, reply_markup=features.set_user_info.kb)


@router.message(UserForm.name)
async def error_form_name(msg: Message) -> None:
    await msg.answer(Errors.text_form, reply_markup=features.cancel_ftr.kb)


@router.message(UserForm.info)
async def error_form_info(msg: Message) -> None:
    await msg.answer(Errors.text_form, reply_markup=features.cancel_ftr.kb)


@router.message(UserForm.photo)
async def error_form_photo(msg: Message) -> None:
    await msg.answer(Errors.photo_form, reply_markup=features.cancel_ftr.kb)


# -------------------------------------------- GAME HANDLERS ----------------------------------------------------------
@router.message_handler(Text(equals=features.rating_ftr.triggers, ignore_case=True), registered=True)
async def rating(msg: types.Message) -> None:
    user = await db.get_user(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
    all_users = await db.get_all_users()
    total_taps = sum([i.taps for i in all_users])
    text = features.rating_ftr.text.format(user_taps=user.taps, total_taps=total_taps)  # type: ignore[union-attr]
    await msg.answer(text, reply_markup=features.rating_ftr.kb)
    if all_users and (best_user := all_users[0]).taps > 0:
        text = features.rating_ftr.text2.format(  # type: ignore[union-attr]
            name=best_user.name, username=best_user.username, info=best_user.info
        )
        await msg.answer(text, reply_markup=features.rating_ftr.kb)
        await bot_safe_send_photo(dp, msg.from_user.id, best_user.photo, reply_markup=features.rating_ftr.kb)


@router.message_handler(Text(equals=features.press_button_ftr.triggers, ignore_case=True), registered=True)
async def send_press_button(msg: types.Message) -> None:
    text, keyboard = await update_button_tap(taps=0)
    await msg.answer(text, reply_markup=Feature.create_tg_inline_kb(keyboard))


@router.callback_query_handler(game_cb.filter(action=features.press_button_ftr.callback_action), registered=True)
async def count_button_tap(callback: types.CallbackQuery, callback_data: dict[Any, Any]) -> None:
    current_taps = int(callback_data["taps"])
    new_taps = current_taps + 1
    await db.incr_user_taps(tg_user=TgUser(tg_id=callback.from_user.id, username=callback.from_user.username))
    text, keyboard = await update_button_tap(taps=new_taps)
    await bot_edit_callback_message(dp, callback, text, reply_markup=Feature.create_tg_inline_kb(keyboard))


async def update_button_tap(*, taps: int) -> tuple[str, list[list[InlineButton]]]:
    text = features.press_button_ftr.text.format(last_session=taps)  # type: ignore[union-attr]
    keyboard = [
        [
            InlineButton(
                text=features.press_button_ftr.button,
                callback_data=game_cb.new(action=features.press_button_ftr.callback_action, taps=taps),
            )
        ],
        [
            InlineButton(
                text=features.start_ftr.button,
                callback_data=game_cb.new(action=features.start_ftr.callback_action, taps=taps),
            )
        ],
    ]
    return text, keyboard


# -------------------------------------------- SERVICE HANDLERS -------------------------------------------------------
@router.message_handler(content_types=["any"], not_registered=True)
async def registration(msg: types.Message) -> types.Message | None:
    if settings.register_passphrase is not None:
        if msg.text.lower() != settings.register_passphrase:
            return await msg.answer(Errors.please_register, reply_markup=features.empty.kb)
        if not msg.from_user.username:
            return await msg.answer(Errors.register_failed, reply_markup=features.empty.kb)
    # user registration
    await db.create_user(tg_user=TgUser(tg_id=msg.from_user.id, username=msg.from_user.username))
    await msg.answer(features.register_ftr.text)
    await main_menu(from_user_id=msg.from_user.id)
    return None


@router.message_handler(content_types=["any"], registered=True)
async def handle_wrong_text_msg(msg: types.Message) -> None:
    await asyncio.sleep(2)
    await msg.reply(Errors.text)


@router.my_chat_member_handler()
async def handle_my_chat_member_handlers(msg: types.Message):
    logger.info(msg)  # уведомление о блокировке


@router.errors_handler(exception=BotBlocked)
async def exception_handler(update: types.Update, exception: BotBlocked):
    # работает только для хендлеров бота, для шедулера не работает
    logger.info(update.message.from_user.id)  # уведомление о блокировке
    logger.info(exception)  # уведомление о блокировке
    return True


# ---------------------------------------- SCHEDULED FEATURES ---------------------------------------
async def healthcheck() -> None:
    logger.info(features.ping_ftr.text2)
    if settings.creator_id is not None:
        await bot_safe_send_message(dp, int(settings.creator_id), features.ping_ftr.text2)  # type: ignore[arg-type]


# -------------------------------------------- BOT SETUP --------------------------------------------
async def bot_scheduler() -> None:
    logger.info("Scheduler is up")
    aioschedule.every().day.at(settings.schedule_healthcheck).do(healthcheck)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher: DbDispatcher) -> None:
    logger.info("Bot is up")
    await bot_safe_send_message(dp, settings.creator_id, "Bot is up")

    # bot commands setup
    cmds = Feature.commands_to_set
    bot_commands = [types.BotCommand(ftr.slashed_command, ftr.slashed_command_descr) for ftr in cmds]
    await dispatcher.bot.set_my_commands(bot_commands)

    # scheduler startup
    asyncio.create_task(bot_scheduler())


async def on_shutdown(dispatcher: DbDispatcher) -> None:
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

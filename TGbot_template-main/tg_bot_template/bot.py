import asyncio
from typing import Any

import aioschedule
from aiogram import types
from aiogram.exceptions import BotBlocked
from aiogram.filters import StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
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


# -------------------------------------------- BASE HANDLERS ----------------------------------------------------------
@dp.message(lambda message: features.ping_ftr.find_triggers(message))
async def ping(msg: types.Message) -> None:
    await bot_safe_send_message(dp, msg.from_user.id, features.ping_ftr.text)  # type: ignore[arg-type]


@dp.message(lambda message: features.creator_ftr.find_triggers(message), CreatorFilter(creator=True))
async def creator_filter_check(msg: types.Message) -> None:
    await msg.answer(features.creator_ftr.text, parse_mode=types.ParseMode.MARKDOWN)


@dp.message(Text(equals=features.cancel_ftr.triggers, ignore_case=True), StateFilter(None))
async def cancel_command(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(features.cancel_ftr.text)
    if await state.get_state() is not None:
        await state.finish()
    await main_menu(from_user_id=msg.from_user.id)


@dp.callback_query(Text(equals=features.cancel_ftr.triggers, ignore_case=True), StateFilter(None))
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await bot_edit_callback_message(dp, callback, features.cancel_ftr.text)
    if await state.get_state() is not None:
        await state.finish()
    await main_menu(from_user_id=callback.from_user.id)


@dp.callback_query(game_cb.filter(action=features.start_ftr.callback_action), RegistrationFilter(registered=True))
@dp.message(Text(equals=features.start_ftr.triggers, ignore_case=True), RegistrationFilter(registered=True))
async def start(msg: types.Message | types.CallbackQuery) -> None:
    await main_menu(from_user_id=msg.from_user.id)
    if isinstance(msg, types.CallbackQuery):
        await msg.answer()


@dp.message(Text(equals=features.help_ftr.triggers, ignore_case=True), RegistrationFilter(registered=True))
async def help_feature(msg: types.Message) -> None:
    await msg.answer(features.help_ftr.text, reply_markup=features.empty.kb)


async def main_menu(*, from_user_id: int) -> None:
    text = f"{features.start_ftr.text}\n\n{features.start_ftr.menu.text}"  # type: ignore[union-attr]
    await bot_safe_send_message(dp, from_user_id, text, reply_markup=features.start_ftr.kb)


# -------------------------------------------- PROFILE HANDLERS -------------------------------------------------------
@dp.message(Text(equals=features.set_user_info.triggers, ignore_case=True), RegistrationFilter(registered=True))
async def set_name(msg: types.Message) -> None:
    await msg.answer(features.set_user_info.text, reply_markup=features.cancel_ftr.kb)
    await UserForm.name.set()


@dp.message(StateFilter(UserForm.name), content_types=["text", "caption"])
async def add_form_name(msg: types.Message, state: FSMContext) -> None:
    await fill_form(msg=msg, feature=features.set_user_name, form=UserForm, state=state)


@dp.message(StateFilter(UserForm.info), content_types=["text", "caption"])
async def add_form_info(msg: types.Message, state: FSMContext) -> None:
    await fill_form(msg=msg, feature=features.set_user_about, form=UserForm, state=state)


async def fill_form(*, msg: types.Message, feature: Feature, form: type[StatesGroup], state: FSMContext) -> None:
    async with state.proxy() as data:
        data[feature.data_key] = msg.caption or msg.text
    await form.next()
    await msg.answer(feature.text, reply_markup=features.cancel_ftr.kb)


@dp.message(StateFilter(UserForm.photo), content_types=["photo"])
async def add_form_photo(msg: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        user_form_data = UserFormData(
            name=data[features.set_user_name.data_key],
            info=data[features.set_user_about.data_key],
            photo=msg.photo[-1].file_id,
        )
        tg_user = TgUser(tg_id=msg.from_user.id, username=msg.from_user.username)
        await db.update_user_info(tg_user=tg_user, user_form_data=user_form_data)
    await state.finish()
    await msg.answer(features.set_user_info.text2, reply_markup=features.set_user_info.kb)


@dp.message(StateFilter(UserForm.name), content_types=["any"])
async def error_form_name(msg: types.Message) -> None:
    await msg.answer(Errors.text_form, reply_markup=features.cancel_ftr.kb)


@dp.message(StateFilter(UserForm.info), content_types=["any"])
async def error_form_info(msg: types.Message) -> None:
    await msg.answer(Errors.text_form, reply_markup=features.cancel_ftr.kb)


@dp.message(StateFilter(UserForm.photo), content_types=["any"])
async def error_form_photo(msg: types.Message) -> None:
    await msg.answer(Errors.photo_form, reply_markup=features.cancel_ftr.kb)


# -------------------------------------------- GAME HANDLERS ----------------------------------------------------------
@dp.message(Text(equals=features.rating_ftr.triggers, ignore_case=True), RegistrationFilter(registered=True))
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


@dp.message(Text(equals=features.press_button_ftr.triggers, ignore_case=True), RegistrationFilter(registered=True))
async def send_press_button(msg: types.Message) -> None:
    text, keyboard = await update_button_tap(taps=0)
    await msg.answer(text, reply_markup=Feature.create_tg_inline_kb(keyboard))


@dp.callback_query(
    game_cb.filter(action=features.press_button_ftr.callback_action),
    RegistrationFilter(registered=True),
)
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
@dp.message(NonRegistrationFilter(not_registered=True), content_types=["any"])
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


@dp.message(RegistrationFilter(registered=True), content_types=["any"])
async def handle_wrong_text_msg(msg: types.Message) -> None:
    await asyncio.sleep(2)
    await msg.reply(Errors.text)


@dp.my_chat_member()
async def handle_my_chat_member_handlers(msg: types.Message):
    logger.info(msg)  # уведомление о блокировке


@dp.errors()
async def exception_handler(update: types.Update, exception: Exception):
    if not isinstance(exception, BotBlocked):
        return False
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


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(dp.bot)


if __name__ == "__main__":
    asyncio.run(main())

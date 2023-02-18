from pyrogram import Client , filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from db import User
from utils import texts
from utils.filters import user_step
from pytorjoman import Account, errors

@Client.on_message(filters.command(['start']))
async def start(_, msg: Message):
    if await User.objects.filter(user_id=msg.from_user.id).exists():        
        await msg.reply("Hi")
    else:
        await User.objects.create(
            user_id=msg.from_user.id,
            send_time= "18:00",
            number_of_words=5
        )
    await msg.reply(texts.LOGIN_OR_REGISTER,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(texts.LOGIN, "login"), InlineKeyboardButton(texts.REGISTER, "register")]
                ]
            )
    )


@Client.on_callback_query(filters.regex('^login$'))
async def ask_for_username(_, cb: CallbackQuery):
    user = await User.objects.get(user_id=cb.from_user.id)
    user.data['step'] = "get_username"
    await user.update(['data'])
    await cb.edit_message_text(texts.SEND_USERNAME)


@Client.on_message(filters.text & user_step("get_username") & filters.reply)
async def get_username(_, msg: Message):
    if len(msg.text) < 5:
        await msg.reply_to_message.edit(texts.FIELD_LENGTH.format(texts.USERNAME, 5, texts.SEND_USERNAME))
        await msg.delete()
        return
    user = await User.objects.get(user_id=msg.from_user.id)
    user.data = {
        'step': 'get_password',
        'login': {
            'username': msg.text,
        }
    }
    await user.update(['data'])
    await msg.reply_to_message.edit(texts.SEND_PASSWORD)
    await msg.delete()
    
@Client.on_message(filters.text & user_step("get_password") & filters.reply)
async def get_password(c, msg: Message):
    if len(msg.text) < 8:
        await msg.reply_to_message.edit(texts.FIELD_LENGTH.format(texts.PASSWORD, 5, texts.SEND_USERNAME))
        await msg.delete()
        return
    user = await User.objects.get(user_id=msg.from_user.id)
    try:
        u = await Account.login(c.torjoman, user.data['login']['username'], msg.text)
    except errors.IncorrectPasswordError or errors.NotFoundError:
        await msg.reply(texts.INCORRECT_PASSWORD)
        await msg.reply_to_message.delete(); await msg.delete()
        user.data['step'] = "get_username"
        await user.update(['data'])
        return
    user.data = {
        'step': "main"
    }
    user.access_token = u._access_token
    user.refresh_token = u._refresh_token
    await user.update()
    await msg.reply_to_message.edit(texts.LOGGED_IN.format(name=u.first_name))
    await msg.delete()
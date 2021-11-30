import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)


API_TEXT = """Hi, {}.
 👋 Tôi có thể tạo phiên chuỗi pyrogram cho tài khoản Telegram của bạn.

Gửi cho tôi /help để biết thêm thông tin

Gửi cho tôi `API_ID` để bắt đầu tạo phiên.
"""



HASH_TEXT = "Bây giờ gửi của bạn `API_HASH`.\n\nNhấn /cancel hủy tác vụ."
PHONE_NUMBER_TEXT = (
    "Bây giờ hãy gửi Số điện thoại của tài khoản Telegram!\n"
    "Bao gồm cả mã Quốc gia. Thí dụ: **+84123456789**\n\n"
    "Nhấn /cancel hủy tác vụ."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` không có hiệu lực.\nNhấp /start để bắt đầu lại.")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`API_HASH` không có hiệu lực.\nNhấp /start để bắt đầu lại.")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`Xác nhận "{phone}" có phải là số chính xác? (y/n):` \n\nGửi: `y` (Xác nhận)\nGửi: `n` (Không đúng)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nNhấn /start để Bắt đầu lại.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"Bạn có Floodwait trong {e.x} Seconds")
        return
    except ApiIdInvalid:
        await msg.reply("ID API và API Hash không hợp lệ.\n\nNhấp /start để Bắt đầu lại.")
        return
    except PhoneNumberInvalid:
        await msg.reply("Số điện thoại của bạn không hợp lệ.\n\nNhấp /start để Bắt đầu lại.")
        return
    try:
        otp = await bot.ask(
            chat.id, ("Một OTP được gửi đến số điện thoại của bạn, "
                      "Vui lòng nhập OTP vào với định dạng `1 2 3 4 5` __(Khoảng trắng giữa mỗi số!)__ \n\n"
                      "Nếu Bot không gửi OTP thì hãy thử /restart và Bắt đầu lại Nhiệm vụ với lệnh /start cho Bot.\n"
                      "Nhấn /cancel hủy tác vụ."), timeout=300)

    except TimeoutError:
        await msg.reply("Đã đạt đến giới hạn thời gian là 5 phút.\nNhấp /start để Bắt đầu lại.")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("Mã không hợp lệ.\n\nNhấp /start để Bắt đầu lại.")
        return
    except PhoneCodeExpired:
        await msg.reply("Mã đã hết hạn.\n\nNhấp /start để Bắt đầu lại.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "Tài khoản của bạn có Xác minh hai bước.\nVui lòng nhập Mật khẩu của bạn.\n\nNhấn /cancel để Hủy.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Đã đạt đến giới hạn thời gian là 5 phút.\n\nNhấp /start để bắt đầu lại.`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION\n\n```{session_string}``` \n\nBy [@owogram](tg://openmessage?user_id=2061163663)")
        await client.disconnect()
        text = "✅ Xin chúc mừng! Phiên chuỗi pyrogram cho tài khoản Telegram của bạn đã được tạo thành công. Bạn có thể tìm thấy phiên chuỗi trong phần tin nhắn đã lưu trong tài khoản telegram của mình. Cảm ơn bạn đã sử dụng tôi! 🤖."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🔥 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 🔥", url=f"https://t.me/owogram")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("Restarted Bot!")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hi, {msg.from_user.mention}. Đây là Bot tạo chuỗi phiên Pyrogram. \
Tôi sẽ đưa cho bạn `STRING_SESSION` cho UserBot của bạn.
Nó cần `API_ID`, `API_HASH`, số điện thoại và Mã xác minh một lần.\
Nó sẽ được gửi đến Số điện thoại của bạn.
Bạn phải đặt **OTP** trong định dạng này: `1 2 3 4 5` __(Khoảng cách giữa mỗi số!)__
**LƯU Ý:** Nếu bot không gửi OTP đến số điện thoại của bạn gửi /restart và nhấp /start để Bắt đầu Quy trình của bạn.
Must Join Channel for Bot Updates !!
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('𝘽𝙤𝙩𝙨 𝙎𝙪𝙥𝙥𝙤𝙧𝙩', url='https://t.me/owogram_support'),
                InlineKeyboardButton('𝘿𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧', url='https://t.me/gimsuri')
            ],
            [
                InlineKeyboardButton('🔥 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 🔥 ', url='https://t.me/owogram'),
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Quá trình đã bị hủy.")
        return True
    return False

if __name__ == "__main__":
    bot.run()

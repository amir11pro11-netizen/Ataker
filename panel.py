from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import uuid

# ================= تنظیمات ربات =================
BOT_TOKEN = "8314851018:AAGL3pRLepwAwBW7iaGqk73IJXICg7ywL8o"
API_ID = 28039994
API_HASH = "00877cdcd706564a4de6abf7f7d64349"

app = Client("panel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= تعریف بخش‌ها =================
# هر بخش: عنوان، متن، دستورات، دکمه‌ها
panels = {
    "main": {
        "text": "**به پنل اتکر ساز رايگان خوش اومديد ربات : @ataksazbot**",
        "buttons": [
            ("📂 فهرست فحش‌ها", "fosh"),
            ("👥 دشمنان", "enemy"),
            ("🛡 ادمین‌ها", "admin"),
            ("⚡ سرعت", "speed"),
            ("▶️ شروع منشن", "start_mention"),
            ("⏹ توقف منشن", "stop_mention"),
            ("💬 اسپم", "spam"),
            ("📊 پینگ", "ping"),
            ("♻️ آپدیت", "update"),
            ("🔗 Join / Left", "joinleft"),
            ("👤 مدیریت اکانت", "account"),
            ("❌ بستن", "close")
        ]
    },
    "fosh": {"text": "➲ `foshlist` [reply]\n**__ریپلای کردن روی فایل فحش برای منشن__**\n➲ `dfoshlist`\n**__حذف کردن تمام فحش های اد شده__**\n➲ `addfosh` [text]\n**__اضافه کردن فحش با متن__**"},
    "enemy": {"text": "➲ `enemy` [reply/ID]\n**__اضافه کردن دشمن منشن با ریپلای یا آیدی عددی__**\n➲ `delenemy` [reply/ID]\n**__حذف کردن دشمن اضافه شده با ریپلای یا آیدی عددی__**\n➲ `clearenemy`\n**__حذف کردن تمام دشمن ها__**"},
    "admin": {"text": "➲ admin [reply]\n**__ریپلای کردن روی کاربر برای ادمین شدن__**\n➲ dadmin [reply]\n**__حذف کردن  ادمین اضافه شده با ریپلای__**\n➲ clearadmin\n**__حذف کردن تمام ادمین های اضافه شده حتی شما__**"},
    "speed": {"text": "➲ `setspeed` [ثانیه]\n**__ست کردن سرعت ارسال بین پیام های منشن__**"},
    "start_mention": {"text": "➲ `start`\n**__شروع کردن منشن__**\n➲ `set`\n**__ست کردن منشن برای جای فعلی__**"},
    "stop_mention": {"text": "➲ `stop`\n**__توقف منشن__**\n➲ `set`\n**__ست کردن جای فعلی برای منشن__**"},
    "spam": {"text": "➲ `spam` [تعداد] [متن]\n**__اسپم کردن متن مورد نیاز با تعداد مشخص شده__**"},
    "ping": {"text": "➲ `ping`\n**__نمایش پینگ ربات__**"},
    "update": {"text": "➲ `restart`\n**__آپدیت ربات__**"},
    "joinleft": {"text": "➲ `join` [reply]\n**__جوین شدن به لینک یا یوزرنیم ریپلای شده__**\n➲ `left` [reply]\n**__لفت دادن از لینک یا یوزرنیم ریپلای شده__**"},
    "account": {"text": "➲ `setname` [text]\n**__عوض کردن اسم اکانت__**\n➲ `setbio` [text]\n**__عوض کردن بیوگرافی اکانت__**\n➲ `setprof` [reply]\n**__ریپلای کردن روی عکس مورد نظر برای پروفایل__**"}
}

# ================= ساخت کیبورد =================
def build_keyboard(section, per_row=2):  # per_row = تعداد دکمه در هر ردیف
    if section not in panels:
        return None

    buttons = panels[section].get("buttons")
    if not buttons:
        # بخش‌هایی که فقط متن دارن → فقط دکمه بازگشت
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main")]])

    # مرتب‌سازی دکمه‌ها در ردیف‌ها
    keyboard = []
    row = []
    for i, (text, data) in enumerate(buttons, start=1):
        row.append(InlineKeyboardButton(text, callback_data=data))
        if i % per_row == 0:  # وقتی به per_row رسید، یه ردیف بساز
            keyboard.append(row)
            row = []
    if row:  # اگه دکمه اضافی موند
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)
# ================= بررسی ادمین =================
def is_admin(user_id):
    try:
        with open("admins.txt", "r") as f:
            admins = f.read().splitlines()
        return str(user_id) in admins
    except FileNotFoundError:
        return False

# ================= Inline Query =================
@app.on_inline_query()
async def inline_panel(client, inline_query):
    if "panel" not in inline_query.query.lower():
        return
    if not is_admin(inline_query.from_user.id):
        return await inline_query.answer([], cache_time=0, switch_pm_text="⚠️ شما اجازه استفاده از ربات را ندارید!", switch_pm_parameter="noaccess")
    keyboard = build_keyboard("main")
    await inline_query.answer([
        InlineQueryResultArticle(
            title="**Amir Ataker Panel**",
            input_message_content=InputTextMessageContent(panels["main"]["text"]),
            reply_markup=keyboard,
            id=str(uuid.uuid4())
        )
    ], cache_time=0, is_personal=True)

# ================= Callback Query =================
@app.on_callback_query()
async def callback(client, callback_query):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⚠️ شما اجازه استفاده از این پنل را ندارید!", show_alert=True)
        return

    data = callback_query.data

    if data == "close":
        try:
            if callback_query.message:
                await callback_query.message.edit("**Closed!**", reply_markup=None)
            elif callback_query.inline_message_id:
                await client.edit_inline_text(
                    inline_message_id=callback_query.inline_message_id,
                    text="**Closed!**",
                    reply_markup=None
                )
        except Exception as e:
            print("❌ Error closing:", e)
            await callback_query.answer("⚠️ خطا در بستن پیام.", show_alert=True)
        else:
            await callback_query.answer()
        return

    # نمایش بخش مورد نظر
    text = panels.get(data, {"text": "❌ بخش نامشخص"})["text"]
    keyboard = build_keyboard(data)
    try:
        if callback_query.message:
            await callback_query.message.edit(text, reply_markup=keyboard)
        elif callback_query.inline_message_id:
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=text,
                reply_markup=keyboard
            )
    except Exception as e:
        print("❌ Error editing message:", e)
        await callback_query.answer("⚠️ خطا در ویرایش پیام.", show_alert=True)
    else:
        await callback_query.answer()

# ================= اجرای ربات =================
print("🚀 PanelBot is running...")
app.run()


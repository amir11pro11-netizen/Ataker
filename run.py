import os
import asyncio
import random
import time
from pyrogram import Client, filters
from pyrogram.types import Message

# ================== تنظیمات اولیه ==================
api_id = 28039994
api_hash = "00877cdcd706564a4de6abf7f7d64349"

app = Client("amir", api_id=api_id, api_hash=api_hash)

OWNER_ID = 7619802938  # آی‌دی شما
ADMINS_FILE = "admins.txt"
FOSH_FILE = "Fosh2928.txt"
ENEMY_FILE = "enemy.txt"
SPEED_FILE = "speed.txt"
CHAT_FILE = "chatid.txt"

# ================== متغیرهای ربات ==================
fosh_list = []
enemy_list = []
admins_list = []
speed = 1.0
mention_task = None
mention_active = False
current_chat_id = None

# ================== مدیریت فایل‌ها ==================
def load_list(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_list(file_path, data_list):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(str(x) for x in data_list))

def load_fosh():
    global fosh_list
    fosh_list = load_list(FOSH_FILE)

def save_fosh():
    save_list(FOSH_FILE, fosh_list)

def load_enemy():
    global enemy_list
    if os.path.exists(ENEMY_FILE):
        with open(ENEMY_FILE, "r", encoding="utf-8") as f:
            enemy_list[:] = [int(line.strip()) for line in f if line.strip()]
    else:
        enemy_list.clear()

def save_enemy():
    save_list(ENEMY_FILE, enemy_list)

def load_speed():
    global speed
    if os.path.exists(SPEED_FILE):
        try:
            with open(SPEED_FILE, "r") as f:
                speed = float(f.read().strip())
        except:
            speed = 1.0

def save_speed():
    with open(SPEED_FILE, "w") as f:
        f.write(str(speed))

def load_admins():
    global admins_list
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            admins_list[:] = [int(line.strip()) for line in f if line.strip()]
    else:
        admins_list.clear()

def save_admins():
    save_list(ADMINS_FILE, admins_list)

# ================== بررسی دسترسی ==================
def is_admin(user_id):
    return user_id == OWNER_ID or user_id in admins_list
# ================== دستور ریستارت ==================
import shutil
import subprocess
import sys

@app.on_message(filters.command(["restart"], prefixes="."))
async def restart_bot(client, message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.reply("♻️ در حال ریستارت و جایگزینی run.py...")

    # مسیر run.py اصلی در ترموکس
    termux_home = os.path.expanduser("~")
    main_run = os.path.join(termux_home, "run.py")

    if not os.path.exists(main_run):
        await message.reply("❌ فایل run.py در مسیر اصلی پیدا نشد!")
        return

    # مسیر فایل فعلی amir.py
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    # نام موقت برای کپی run.py
    temp_run = os.path.join(current_dir, "run_temp.py")

    try:
        # کپی run.py به مسیر فعلی
        shutil.copy(main_run, temp_run)

        # اجرای فایل موقت
        subprocess.Popen([sys.executable, temp_run])

        # حذف amir.py قبلی
        os.remove(current_file)

        # تغییر نام فایل موقت به amir.py
        os.rename(temp_run, os.path.basename(current_file))

    except Exception as e:
        await message.reply(f"❌ خطا هنگام ریستارت: {e}")
        return

    # خروج از اسکریپت فعلی
    os._exit(0)
# ================== منشن دشمن‌ها ==================
def build_enemy_mentions():
    limited = enemy_list[:32]
    mentions = [f"[✯](tg://user?id={user_id})" for user_id in limited]
    return " ".join(mentions)

async def mention_loop(chat_id):
    global mention_active
    try:
        while mention_active:
            if not fosh_list or not enemy_list:
                await asyncio.sleep(1)
                continue

            text = random.choice(fosh_list)  # ارسال تصادفی فحش
            enemy_line = build_enemy_mentions()
            full_text = f"{text}\n\n{enemy_line}"

            await app.send_message(chat_id, full_text, disable_web_page_preview=True)
            await asyncio.sleep(speed)
    except asyncio.CancelledError:
        pass

# ================== دستورات ==================
@app.on_message(filters.command(["foshlist"], prefixes=".") & filters.reply)
async def set_foshlist(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("📂 Please reply to a file containing fosh list.")
        return
    file = await message.reply_to_message.download()
    with open(file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    fosh_list.extend(lines)
    fosh_list[:] = list(dict.fromkeys(fosh_list))
    save_fosh()
    await message.reply(f"✅ {len(lines)} fosh added. Total: {len(fosh_list)}")

@app.on_message(filters.command(["dfoshlist"], prefixes="."))
async def del_foshlist(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    fosh_list.clear()
    save_fosh()
    await message.reply("🗑 Fosh list cleared.")

@app.on_message(filters.command(["enemy"], prefixes="."))
async def add_enemy(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            user_id = int(message.command[1])
        except:
            pass
    if not user_id:
        await message.reply("⚠️ Reply to a user or provide ID.")
        return
    if user_id in enemy_list:
        await message.reply("⚠️ User already an enemy.")
        return
    if len(enemy_list) >= 32:
        await message.reply("⚠️ Maximum 32 enemies allowed.")
        return
    enemy_list.append(user_id)
    save_enemy()
    await message.reply(f"✅ Enemy added ({len(enemy_list)}/32)")

@app.on_message(filters.command(["delenemy"], prefixes="."))
async def del_enemy(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            user_id = int(message.command[1])
        except:
            pass
    if not user_id:
        await message.reply("⚠️ Reply to a user or provide ID.")
        return
    if user_id not in enemy_list:
        await message.reply("⚠️ User is not an enemy.")
        return
    enemy_list.remove(user_id)
    save_enemy()
    await message.reply(f"🗑 Enemy removed ({len(enemy_list)}/32)")

@app.on_message(filters.command(["clearenemy"], prefixes="."))
async def clear_enemy_list(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    enemy_list.clear()
    save_enemy()
    await message.reply("🗑 All enemies cleared.")

@app.on_message(filters.command(["setspeed"], prefixes="."))
async def set_speed_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    try:
        spd = float(message.command[1])
        if spd < 0:
            await message.reply("⚠️ Speed cannot be negative.")
            return
        global speed
        speed = spd
        save_speed()
        await message.reply(f"⚡ Speed set to {speed} seconds.")
    except:
        await message.reply("⚠️ Correct format: .setspeed 1.0")

@app.on_message(filters.command(["start"], prefixes="."))
async def start_mention(client, message: Message):
    global mention_active, mention_task, current_chat_id
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    if mention_active:
        await message.reply("⚠️ Mention already active.")
        return
    if not fosh_list:
        await message.reply("⚠️ Fosh list is empty.")
        return
    if not enemy_list:
        await message.reply("⚠️ Enemy list is empty.")
        return
    if not current_chat_id:
        current_chat_id = message.chat.id
    mention_active = True
    mention_task = asyncio.create_task(mention_loop(current_chat_id))
    await message.reply("❊ mention started.")

@app.on_message(filters.command(["stop"], prefixes="."))
async def stop_mention(client, message: Message):
    global mention_active, mention_task
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    if not mention_active:
        await message.reply("⚠️ Mention not active.")
        return
    mention_active = False
    if mention_task:
        mention_task.cancel()
        mention_task = None
    await message.reply("❊ Mention stopped.")

# ================== مدیریت ادمین‌ها ==================
@app.on_message(filters.command(["admin"], prefixes=".") & filters.reply)
async def add_admin(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    user_id = message.reply_to_message.from_user.id
    if user_id in admins_list:
        await message.reply("⚠️ User already admin. Use .dadmin to remove.")
        return
    admins_list.append(user_id)
    save_admins()
    await message.reply(f"✅ User {user_id} added as admin.")

@app.on_message(filters.command(["dadmin"], prefixes=".") & filters.reply)
async def remove_admin(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()
    user_id = message.reply_to_message.from_user.id
    if user_id not in admins_list:
        await message.reply("⚠️ User is not an admin.")
        return
    admins_list.remove(user_id)
    save_admins()
    await message.reply(f"🗑 User {user_id} removed from admins.")

# ================== دستورات جدید ==================
@app.on_message(filters.command(["set"], prefixes="."))
async def set_chat_cmd(client, message: Message):
    global current_chat_id
    if not is_admin(message.from_user.id):
        return
    current_chat_id = message.chat.id
    save_list(CHAT_FILE, [current_chat_id])
    await message.reply(f"✅ Chat ID set to {current_chat_id}")

@app.on_message(filters.command(["id"], prefixes=".") & filters.reply)
async def get_user_id(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    user_id = message.reply_to_message.from_user.id
    await message.reply(f"🆔 User ID: `{user_id}`")

# نمایش فحش‌ها
@app.on_message(filters.command(["foshlists"], prefixes="."))
async def show_foshlist(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if not fosh_list:
        await message.reply("⚠️ Fosh list is empty.")
        return
    text = "📂 Fosh list:\n\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(fosh_list[:50])])
    if len(fosh_list) > 50:
        text += f"\n\n... and {len(fosh_list)-50} more"
    await message.reply(text)

# پاک کردن کل ادمین‌ها
@app.on_message(filters.command(["clearadmin"], prefixes="."))
async def clear_admins_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    admins_list.clear()
    save_admins()
    await message.reply("🗑 All admins cleared.")

# اسپم
@app.on_message(filters.command(["spam"], prefixes="."))
async def spam_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        count = int(message.command[1])
        text = " ".join(message.command[2:])
    except:
        await message.reply("⚠️ Usage: .spam 10 salam")
        return
    if count > 50:
        await message.reply("⚠️ Maximum 50 messages allowed.")
        return
    for i in range(count):
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(1.2)

# پینگ
@app.on_message(filters.command(["ping"], prefixes="."))
async def ping_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    start = time.time()
    m = await message.reply("Ping...")
    end = time.time()
    ms = int((end - start) * 1000)
    await m.edit(f"Ping : `{ms}`")

# ================== پنل ==================
@app.on_message(filters.command(["panel"], prefixes="."))
async def panel_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.delete()

    try:
        # گرفتن نتایج اینلاین از بات دوم
        results = await app.get_inline_bot_results("helperatakerbot", "panel")

        if results.results:
            # انتخاب اولین نتیجه
            first_result_id = results.results[0].id
            # ارسال همون نتیجه توی چت
            await app.send_inline_bot_result(
                chat_id=message.chat.id,
                query_id=results.query_id,
                result_id=first_result_id
            )
        else:
            await app.send_message(message.chat.id, "⚠️ نتیجه‌ای از @helperatakerbot پیدا نشد.")

    except Exception as e:
        await app.send_message(message.chat.id, f"❌ خطا: {e}")
# ================== بارگذاری داده‌ها ==================
load_fosh()
load_enemy()
load_speed()
load_admins()

if os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "r") as f:
        try:
            current_chat_id = int(f.read().strip())
        except:
            current_chat_id = None

print("Bot is running...")
app.run()

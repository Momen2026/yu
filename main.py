import os
import glob
import re
import uuid 
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import time

# ------------------------------
# إعدادات البوت والملفات
# ------------------------------
API_ID = 10623040
API_HASH = "ec3e3c791d8e5b4b37f8088b82709868"
BOT_TOKEN = "7421416273:AAGzxlpGhicJTE8sghJG-uZK1CoO4GUOEsw"

COOKIE_FILE = "cookies.txt" # اسم ملف الكوكيز
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

bot = Client("media_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🆕 قاموس لتخزين الروابط مؤقتاً باستخدام UUID قصير (حل مشكلة Button Data Too Large)
temp_data = {} 

# ------------------------------
# دوال yt-dlp للتحميل والاستخراج
# ------------------------------

# دالة مساعدة لاستخراج معلومات الفيديو (لم تتغير)
def get_video_info(url, download_thumbnail=False):
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "skip_download": True,
        "writethumbnail": download_thumbnail,
        "outtmpl": f"{DOWNLOADS_DIR}/%(id)s_%(title).15s.%(ext)s" 
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

# استخراج الجودات وصورة مصغرة لليوتيوب (لم تتغير)
def get_youtube_data(url):
    info = get_video_info(url, download_thumbnail=True)
    formats = info.get("formats", [])
    qualities = sorted(set(f["height"] for f in formats if f.get("height")))
    
    thumbnail_path = None
    video_id = info.get("id", "")
    title_short = info.get("title", "")[:15]
    
    search_pattern = f"{DOWNLOADS_DIR}/{re.escape(video_id)}_{re.escape(title_short)}*.thumb*"
    files = glob.glob(search_pattern)
    for f in files:
        if f.endswith(('.webp', '.jpg', '.jpeg', '.png')):
            thumbnail_path = f
            break
            
    return [str(q) for q in qualities if q >= 360], thumbnail_path

# تحميل فيديو يوتيوب بجودة محددة (لم تتغير)
def download_youtube_video(url, quality):
    ydl_opts = {
        "format": f"bestvideo[height={quality}]+bestaudio/best",
        "outtmpl": f"{DOWNLOADS_DIR}/%(title)s.%(ext)s",
        "cookiefile": COOKIE_FILE,
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
        "quiet": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = info.get("_filename") or ydl.prepare_filename(info)
        return file_path, info.get("title")

# تحميل صوت بصيغة mp3 أو m4a (مشترك) (لم تتغير)
def download_audio(url, codec="mp3"):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOADS_DIR}/%(id)s_audio_%(title)s.%(ext)s", 
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": "192"
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title")
        performer = info.get("uploader") or info.get("channel") or info.get("artist")

    ext = codec.lower()
    video_id = info.get("id", "")
    search_pattern = f"{DOWNLOADS_DIR}/{re.escape(video_id)}_audio*.{ext}"
    files = glob.glob(search_pattern)
    
    if not files:
        files = glob.glob(f"{DOWNLOADS_DIR}/*.{ext}")

    if files:
        return files[0], title, performer
    
    raise Exception(f"❌ لم يتم العثور على ملف {ext} بعد التحويل.")

# تحميل فيديو بأفضل جودة (لـ فيسبوك، انستغرام، تيك توك، وجميع المنصات الأخرى)
def download_best_video(url):
    ydl_opts = {
        # 🆕 تم تحسين هذا الجزء لضمان الحصول على أفضل فيديو وصوت ودمجها قدر الإمكان
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": f"{DOWNLOADS_DIR}/%(title)s.%(ext)s",
        "cookiefile": COOKIE_FILE, 
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
        "quiet": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = info.get("_filename") or ydl.prepare_filename(info)
        return file_path, info.get("title")

# ------------------------------
# دالة الترحيب الاحترافية (لم تتغير)
# ------------------------------

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_name = message.from_user.first_name
    
    welcome_message = f"""
✨ **أهلاً يا {user_name}!** أنا **Media Master** 🤖
أنا بوت التحميل الأفضل! أرسل رابط، وأحصل على محتواك بجودة عالية **حتى 2 جيجا** دون قيود.

**(مطور: Momen)**

🚀 **المنصات المدعومة:**
* **YouTube:** جودات متعددة وصورة مصغرة 🖼️.
* **Instagram:** فيديو وصوت بجودة عالية.
* **TikTok:** تحميل مباشر أو كـ صوت MP3.
* **Facebook:** تحميل مباشر بأفضل جودة.
* **والعديد من المنصات الأخرى المدعومة من yt-dlp!** 🌐

ابدأ الآن! أرسل لي أول رابط. 👇
"""
    await message.reply_text(welcome_message)

# ------------------------------
# معالجة الرسائل الجديدة (الروابط)
# ------------------------------

@bot.on_message(filters.private & filters.text & ~filters.command("start"))
async def handle_media_link(client, message):
    url = message.text.strip()
    source_name = None

    # 1. روابط إنستغرام 
    instagram_pattern = re.compile(r"(instagram\.com|instagr\.am)/")
    if instagram_pattern.search(url):
        source_name = "إنستغرام"
        short_id = str(uuid.uuid4())[:8] 
        temp_data[short_id] = url
        buttons = [[
            InlineKeyboardButton("فيديو بجودة عالية 🎥", callback_data=f"ig_video|{short_id}"),
            InlineKeyboardButton("صوت (MP3) 🎧", callback_data=f"audio|mp3_ig|{short_id}") 
        ]]
        await message.reply_text(f"📥 **{source_name}**: تم الكشف عن رابط إنستغرام! اختر طريقة التحميل:", reply_markup=InlineKeyboardMarkup(buttons))
        return # 🛑 مهم: العودة لمنع استمرار المعالجة للرابط العام

    # 2. روابط يوتيوب
    youtube_pattern = re.compile(r"(youtube\.com|youtu\.be)/")
    if youtube_pattern.search(url):
        source_name = "يوتيوب"
        msg = await message.reply_text(f"⏳ **{source_name}**: جاري استخراج معلومات الفيديو والصورة المصغرة...")
        try:
            qualities, thumbnail_path = get_youtube_data(url)
            short_id = str(uuid.uuid4())[:8]
            temp_data[short_id] = url
            
            buttons = [[InlineKeyboardButton(f"{q}p 🎥", callback_data=f"yt|{q}|{short_id}")] for q in qualities]
            buttons.append([
                InlineKeyboardButton("🎧 MP3", callback_data=f"audio|mp3_yt|{short_id}"),
                InlineKeyboardButton("🎧 M4A", callback_data=f"audio|m4a_yt|{short_id}")
            ])
            
            caption = f"📥 **{source_name}**: اختر الجودة أو نوع الصوت:"
            
            await msg.delete() 
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                await message.reply_photo(thumbnail_path, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
                os.remove(thumbnail_path) 
            else:
                await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(buttons))
                
        except Exception as e:
            await msg.delete() 
            await message.reply_text(f"❌ خطأ في استخراج معلومات {source_name}. قد يكون الفيديو خاصاً أو محظوراً.\nالخطأ: {e}")
        return # 🛑 مهم: العودة لمنع استمرار المعالجة للرابط العام

    # 3. روابط فيسبوك 
    facebook_pattern = re.compile(r"(facebook\.com|fb\.watch)/")
    if facebook_pattern.search(url):
        source_name = "فيسبوك"
        msg = await message.reply_text(f"⏳ **{source_name}**: جاري بدء التحميل بأفضل جودة...")
        try:
            file_path, title = download_best_video(url)
            if os.path.exists(file_path):
                await message.reply_video(file_path, caption=f"✅ {title} من {source_name} (بأفضل جودة)")
                os.remove(file_path)
            else:
                raise FileNotFoundError(f"الملف لم يتم إنشاؤه في المسار: {file_path}")
        except Exception as e:
            await message.reply_text(f"❌ خطأ أثناء تحميل فيديو {source_name}.\nالخطأ: {e}")
        finally:
            await msg.delete()
        return # 🛑 مهم: العودة لمنع استمرار المعالجة للرابط العام

    # 4. روابط تيك توك 
    tiktok_pattern = re.compile(r"(tiktok\.com)/")
    if tiktok_pattern.search(url):
        source_name = "تيك توك"
        short_id = str(uuid.uuid4())[:8]
        temp_data[short_id] = url
        buttons = [[
            InlineKeyboardButton("فيديو 🎥", callback_data=f"tt_video|{short_id}"),
            InlineKeyboardButton("صوت (MP3) 🎧", callback_data=f"audio|mp3_tt|{short_id}")
        ]]
        await message.reply_text(f"📥 **{source_name}**: اختر طريقة التحميل (الكوكيز مُفعلة):", reply_markup=InlineKeyboardMarkup(buttons))
        return # 🛑 مهم: العودة لمنع استمرار المعالجة للرابط العام

    # 5. 🆕 رابط عام (يدعم أي منصة أخرى تدعمها yt-dlp)
    
    # 🆕 التحقق من أن الرابط ليس مجرد نص غير مفهوم (لمنع رسالة الخطأ الأخيرة)
    # لا نقوم هنا بالتحقق من المنصة بل نعتمد على yt-dlp ليحددها ويحملها مباشرة بأفضل جودة
    
    # رسالة الانتظار للرابط العام
    msg = await message.reply_text("🌐 **تحميل عام**: جاري محاولة التعرف على الرابط وتحميله بأفضل جودة...")
    
    try:
        # استخدام دالة التحميل بأفضل جودة (download_best_video)
        file_path, title = download_best_video(url)
        
        # استخراج اسم المنصة من معلومات الفيديو المحملة (اختياري لتحسين الرد)
        try:
            info = get_video_info(url)
            source_name = info.get("extractor_key") or "منصة غير معروفة"
        except Exception:
            source_name = "منصة أخرى" # في حال فشل الاستخراج قبل التحميل

        if os.path.exists(file_path):
            await message.reply_video(file_path, caption=f"✅ تم التحميل: {title} من **{source_name}** (بأفضل جودة)")
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"الملف لم يتم إنشاؤه في المسار: {file_path}")

    except Exception as e:
        # إذا فشل التحميل كـ فيديو، نحاول استخراج الصوت كـ mp3 كخيار أخير
        try:
            # محاولة استخراج معلومات المنصة مرة أخرى لرسالة الخطأ
            info = get_video_info(url)
            source_name = info.get("extractor_key") or "منصة غير معروفة"
            
            # محاولة تحميل الصوت
            file_path, title, performer = download_audio(url, codec="mp3")
            await message.reply_audio(
                audio=file_path,
                caption=f"⚠️ تعذر تحميل الفيديو. تم إرسال الصوت (MP3) من {source_name}.",
                performer=performer or source_name,
                title=title
            )
            os.remove(file_path)
        except Exception as audio_e:
            # فشل نهائي
            await message.reply_text(f"""
❌ **فشل التحميل!**
البوت لم يتمكن من التعرف على الرابط أو تحميله من تلك المنصة.
**السبب المحتمل:** محتوى خاص، قيود جغرافية، أو المنصة تتطلب كوكيز غير متوفرة.
**الخطأ الأصلي:** {e}
            """)
    finally:
        await msg.delete()
        # لا حاجة للحذف من temp_data هنا لأنه لم يتم تخزين شيء


# ------------------------------
# معالجة الأزرار (Callback Queries) - لم تتغير
# ------------------------------

# تحميل فيديو إنستغرام بجودة عالية 
@bot.on_callback_query(filters.regex(r"^ig_video\|"))
async def handle_instagram_video_download(client, callback_query):
    _, short_id = callback_query.data.split("|")
    url = temp_data.pop(short_id, None) 
    
    if not url:
        await callback_query.answer("⚠️ انتهت صلاحية هذا الرابط. يرجى إرساله مجدداً.", show_alert=True)
        return
        
    source_name = "إنستغرام"
    await callback_query.answer("جاري بدء تحميل الفيديو...", show_alert=False) 
    msg = await callback_query.message.reply_text(f"⏳ **{source_name}**: جاري تحميل الفيديو بأفضل جودة...")
    
    try:
        file_path, title = download_best_video(url)
        if os.path.exists(file_path):
            await callback_query.message.reply_video(file_path, caption=f"✅ {title} من {source_name} (بأفضل جودة)")
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"الملف لم يتم إنشاؤه في المسار: {file_path}")
    except Exception as e:
        await callback_query.message.reply_text(f"❌ خطأ أثناء تحميل فيديو {source_name}. قد يكون خاصاً.\nالخطأ: {e}")
    finally:
        await msg.delete()


# تحميل فيديو يوتيوب بجودة محددة 
@bot.on_callback_query(filters.regex(r"^yt\|"))
async def handle_youtube_download(client, callback_query):
    _, quality, short_id = callback_query.data.split("|")
    url = temp_data.pop(short_id, None) 
    
    if not url:
        await callback_query.answer("⚠️ انتهت صلاحية هذا الرابط. يرجى إرساله مجدداً.", show_alert=True)
        return
        
    await callback_query.answer("جاري بدء التحميل...", show_alert=False)
    msg = await callback_query.message.reply_text(f"⏳ جاري تحميل الفيديو من يوتيوب بجودة {quality}p...")
    
    try:
        file_path, title = download_youtube_video(url, quality)
        if os.path.exists(file_path):
            await callback_query.message.reply_video(file_path, caption=f"✅ {title} ({quality}p) من يوتيوب")
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"الملف لم يتم إنشاؤه في المسار: {file_path}")
    except Exception as e:
        await callback_query.message.reply_text(f"❌ خطأ أثناء تحميل فيديو يوتيوب:\n{e}")
    finally:
        await msg.delete()

# تحميل صوت mp3 أو m4a (مشترك ليوتيوب، تيك توك، إنستغرام) 
@bot.on_callback_query(filters.regex(r"^audio\|"))
async def handle_audio_download(client, callback_query):
    _, codec_source, short_id = callback_query.data.split("|")
    
    codec = "mp3" if "mp3" in codec_source else "m4a"
    url = temp_data.pop(short_id, None)
    
    if not url:
        await callback_query.answer("⚠️ انتهت صلاحية هذا الرابط. يرجى إرساله مجدداً.", show_alert=True)
        return
    
    source_map = {'_yt': 'يوتيوب', '_ig': 'إنستغرام', '_tt': 'تيك توك'}
    source_key = next((k for k in source_map if k in codec_source), 'المصدر')
    source_name = source_map.get(source_key, 'المصدر')

    await callback_query.answer(f"جاري بدء تحميل الصوت ({codec})...", show_alert=False)
    msg = await callback_query.message.reply_text(f"⏳ جاري تحميل الصوت ({codec}) من {source_name}...")
    
    try:
        file_path, title, performer = download_audio(url, codec)
        await callback_query.message.reply_audio(
            audio=file_path,
            caption=f"✅ {title} ({codec.upper()})",
            performer=performer or source_name,
            title=title
        )
        os.remove(file_path)
    except Exception as e:
        await callback_query.message.reply_text(f"❌ خطأ أثناء تحميل الصوت من {source_name}:\n{e}")
    finally:
        await msg.delete()


# تحميل فيديو تيك توك 
@bot.on_callback_query(filters.regex(r"^tt_video\|"))
async def handle_tiktok_video_download(client, callback_query):
    _, short_id = callback_query.data.split("|")
    url = temp_data.pop(short_id, None) 
    
    if not url:
        await callback_query.answer("⚠️ انتهت صلاحية هذا الرابط. يرجى إرساله مجدداً.", show_alert=True)
        return
        
    source_name = "تيك توك"
    await callback_query.answer("جاري بدء تحميل الفيديو...", show_alert=False)
    msg = await callback_query.message.reply_text(f"⏳ جاري تحميل فيديو {source_name} بأفضل جودة...")
    
    try:
        file_path, title = download_best_video(url)
        if os.path.exists(file_path):
            await callback_query.message.reply_video(file_path, caption=f"✅ {title} من {source_name} (بأفضل جودة)")
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"الملف لم يتم إنشاؤه في المسار: {file_path}")
    except Exception as e:
        await callback_query.message.reply_text(f"❌ خطأ أثناء تحميل فيديو {source_name}. قد يكون خاصاً.\nالخطأ: {e}")
    finally:
        await msg.delete()


if __name__ == "__main__":
    print("🤖 البوت يعمل... اضغط Ctrl+C للإيقاف.")
    bot.run()
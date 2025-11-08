import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# تعيين التوكن مباشرة في الكود
TELEGRAMBOTTOKEN = "7504048483:AAFnxYH0WGre21VxYLGUlw9nxU6hrCsor1Y"

if not TELEGRAMBOTTOKEN:
    print("خطأ: لم يتم العثور على التوكن")
    exit()

# إعدادات تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يرسل رسالة ترحيبية عند إرسال الأمر /start."""
    await update.message.reply_text(
        "أهلاً بك! أرسل لي أي رابط، وسأحاول تتبع إعادة التوجيه للعثور على الرابط النهائي.\n"
        "(ملاحظة: هذا البوت لا يدعم المواقع التي تتطلب JavaScript أو CAPTCHA)."
    )

async def handlemessage(update: Update, context: ContextTypes.DEFAULTTYPE):
    """يعالج الرسائل النصية التي تحتوي على روابط."""
    message_text = update.message.text
    if not message_text.startswith('http'):
        await update.message.reply_text("الرجاء إرسال رابط يبدأ بـ http أو https.")
        return

    original_url = message_text
    await update.message.reply_text(f"جاري معالجة الرابط: {original_url}\nالرجاء الانتظار...")

    try:
        # استخدام User-Agent يحاكي متصفح حقيقي
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }

        # استخدام "HEAD" بدلاً من "GET" للتأكد من الحصول على الرؤوس فقط
        response = requests.head(original_url, headers=headers, allow_redirects=True, timeout=10, verify=True)

        final_url = response.url

        if final_url == original_url:
            # إذا كان الرابط النهائي هو نفسه
            await update.message.reply_text(
                "لم يتم العثور على إعادة توجيه.\n"
                f"الرابط النهائي هو نفسه: {final_url}\n"
                "(هذا الموقع يتطلب على الأغلب JavaScript أو خطوة يدوية)."
            )
        else:
            await update.message.reply_text(
                "تم العثور على الرابط النهائي بعد تتبع إعادة التوجيه:\n\n"
                f"الرابط الأصلي:\n{original_url}\n\n"
                f"الرابط المباشر (المحتمل):\n{final_url}",
                parse_mode='Markdown'
            )

    except requests.exceptions.Timeout:
        await update.message.reply_text("فشل: استغرقت العملية وقتاً طويلاً (Timeout).")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing URL {original_url}: {e}")
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الرابط: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await update.message.reply_text("حدث خطأ غير متوقع.")

# تشغيل البوت
def main():
    """الدالة الرئيسية لتشغيل البوت."""
    if not TELEGRAMBOTTOKEN:
        logger.error("التوكن غير موجود. البوت لن يعمل.")
        return

    application = ApplicationBuilder().token(TELEGRAMBOTTOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    # معالجة كل الرسائل النصية التي ليست أوامر
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlemessage))

    logger.info("البوت قيد التشغيل...")
    application.run_polling()

if __name__ == "__main__":
    main()

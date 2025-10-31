import os, zipfile, shutil
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from github import Github

BOT_TOKEN = '8254273392:AAFQ7eT3PqCicbwkhhVpBEI3XmjoxsHnmEU'
GITHUB_TOKEN = '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'

# استخراج اسم المشروع من اسم الملف فقط
def get_project_name(zip_path):
    return os.path.splitext(os.path.basename(zip_path))[0].replace(' ', '-').lower()

# استقبال ملف ZIP من المستخدم
async def handle_zip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc: Document = update.message.document
    if not doc.file_name.endswith('.zip'):
        await update.message.reply_text("📦 أرسل ملف .zip فقط.")
        return

    await update.message.reply_text("📥 جاري تحميل الملف...")
    file = await doc.get_file()
    zip_path = f"{doc.file_name}"
    await file.download_to_drive(zip_path)

    await update.message.reply_text("🧩 جاري فك الضغط والتجهيز...")
    extract_path = 'unzipped'
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # إذا الملفات داخل مجلد واحد، ننقلها إلى الجذر
    subdirs = [d for d in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, d))]
    if len(subdirs) == 1:
        inner_path = os.path.join(extract_path, subdirs[0])
        for item in os.listdir(inner_path):
            shutil.move(os.path.join(inner_path, item), extract_path)
        shutil.rmtree(inner_path)

    project_name = get_project_name(zip_path)
    await update.message.reply_text(f"🛠️ جاري إنشاء الريبو: `{project_name}`")

    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repo = user.create_repo(name=project_name, private=False, auto_init=False)

    await update.message.reply_text("🚀 جاري رفع الملفات إلى GitHub...")

    file_list = []
    for root, _, files in os.walk(extract_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, extract_path).replace('\\', '/')
            file_list.append(rel_path)
            with open(full_path, 'rb') as f:
                content = f.read()
            try:
                repo.create_file(rel_path, f"upload {rel_path}", content)
            except:
                repo.update_file(rel_path, f"update {rel_path}", content, repo.get_contents(rel_path).sha)

    repo_url = f"https://github.com/{user.login}/{project_name}"
    structure = "\n".join([f"📄 {path}" for path in file_list])
    await update.message.reply_text(
        f"✅ تم رفع المشروع بنجاح!\n🔗 رابط الريبو:\n{repo_url}\n\n📁 محتويات المشروع:\n{structure}"
    )

# تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.Document.ALL, handle_zip))
app.run_polling()

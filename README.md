# SAYYAF OSINT BOT

بوت Telegram لتدقيق خصوصية رقم الهاتف المملوك للمستخدم أو الذي لديه موافقة صريحة على فحصه.

## حدود الأداة
لا تكشف الأداة الحسابات المرتبطة برقم الهاتف. منصات التواصل لا توفر واجهة عامة موثوقة تتيح جلب كل الحسابات المرتبطة برقم عشوائي. الأداة تتحقق من صحة تنسيق الرقم فقط وتقدم إرشادات لحماية الخصوصية.

## التشغيل محلياً في Termux
```bash
pkg update -y
pkg install python -y
pip install -r requirements.txt
export BOT_TOKEN="توكن_البوت"
python main.py
```

## النشر على Render
1. ارفع محتويات هذا المجلد إلى مستودع GitHub.
2. في Render اختر New ثم Web Service واربط مستودع GitHub.
3. اجعل Build Command:
   `pip install -r requirements.txt`
4. اجعل Start Command:
   `python main.py`
5. أضف متغير البيئة `BOT_TOKEN` وضع توكن BotFather كقيمة سرية.
6. ابدأ النشر، ثم افتح رابط الخدمة للتأكد من ظهور `status: ok`.

## أوامر البوت
- `/start` البداية
- `/audit` بدء تدقيق الخصوصية
- `/help` المساعدة

لا تضع التوكن داخل ملفات GitHub أو تشاركه مع أي شخص.

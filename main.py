import os
import time
import logging
import threading
import requests
from flask import Flask, jsonify
import phonenumbers
from phonenumbers import PhoneNumberFormat

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sayyaf-bot")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)
offset = 0

WELCOME = (
    "مرحباً بك في SAYYAF OSINT BOT\n\n"
    "هذه أداة لتدقيق خصوصية رقم هاتف تملكه أو لديك موافقة صريحة من صاحبه على فحصه.\n"
    "لا يستطيع البوت كشف جميع الحسابات المرتبطة برقم هاتف؛ هذه البيانات خاصة ولا توفرها "
    "المنصات عبر واجهة عامة موثوقة.\n\n"
    "للبدء أرسل /audit ثم أكد أن الرقم لك أو لديك موافقة صاحبه."
)

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API}/sendMessage", json=payload, timeout=20).raise_for_status()
    except requests.RequestException as exc:
        log.warning("Telegram send failed: %s", exc)

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start":
        send_message(chat_id, WELCOME)
        return

    if text == "/audit":
        keyboard = {
            "inline_keyboard": [[
                {"text": "أؤكد أن الرقم لي أو لدي موافقة صاحبه", "callback_data": "consent_yes"}
            ]]
        }
        send_message(
            chat_id,
            "قبل المتابعة، يرجى تأكيد ملكية الرقم أو وجود موافقة صريحة من صاحبه.",
            keyboard
        )
        return

    if text == "/help":
        send_message(chat_id, "الأوامر المتاحة:\n/start — البداية\n/audit — بدء تدقيق الخصوصية\n/help — المساعدة")
        return

    send_message(
        chat_id,
        "استخدم /audit لبدء تدقيق الخصوصية. لا ترسل أرقام أشخاص آخرين دون موافقتهم."
    )

def handle_callback(callback):
    data = callback.get("data")
    chat_id = callback["message"]["chat"]["id"]
    callback_id = callback["id"]

    try:
        requests.post(
            f"{API}/answerCallbackQuery",
            json={"callback_query_id": callback_id},
            timeout=15
        )
    except requests.RequestException:
        pass

    if data == "consent_yes":
        send_message(
            chat_id,
            "أرسل رقمك بصيغة دولية، مثال: +9677XXXXXXXX.\n"
            "سيتم التحقق من صحة التنسيق فقط؛ لن يتم البحث عن حسابات خاصة أو كشف ارتباطات غير معلنة."
        )

def poll():
    global offset
    while True:
        try:
            response = requests.get(
                f"{API}/getUpdates",
                params={"timeout": 25, "offset": offset},
                timeout=35
            )
            response.raise_for_status()
            for update in response.json().get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    msg = update["message"]
                    text = (msg.get("text") or "").strip()
                    if text.startswith("+") or text.replace(" ", "").isdigit():
                        audit_number(msg["chat"]["id"], text)
                    else:
                        handle_message(msg)
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])
        except requests.RequestException as exc:
            log.warning("Polling error: %s", exc)
            time.sleep(5)
        except Exception:
            log.exception("Unexpected polling error")
            time.sleep(5)

def audit_number(chat_id, raw_number):
    try:
        parsed = phonenumbers.parse(raw_number, None)
        if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
            send_message(chat_id, "الرقم غير صالح أو غير مكتمل. أرسله بالصيغة الدولية مثل +9677XXXXXXXX.")
            return
        normalized = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        region = phonenumbers.region_code_for_number(parsed) or "غير معروف"
        send_message(
            chat_id,
            "تم التحقق من تنسيق الرقم.\n\n"
            f"الرقم بصيغة دولية: {normalized}\n"
            f"رمز المنطقة: {region}\n\n"
            "لم يتم جلب أو تخمين أي حسابات مرتبطة به؛ لا توجد وسيلة عامة موثوقة "
            "تتيح ذلك لجميع منصات التواصل.\n\n"
            "لتدقيق حساباتك بنفسك:\n"
            "1) راجع إعدادات الخصوصية واكتشاف الحساب برقم الهاتف في كل منصة.\n"
            "2) راجع الأجهزة والجلسات النشطة.\n"
            "3) فعّل المصادقة الثنائية.\n"
            "4) لا تشارك رموز التحقق مع أي شخص."
        )
    except phonenumbers.NumberParseException:
        send_message(chat_id, "تعذر فهم الرقم. أرسله بالصيغة الدولية مع رمز الدولة، مثل +9677XXXXXXXX.")

@app.get("/")
def health():
    return jsonify({"status": "ok", "service": "SAYYAF OSINT BOT"})

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("ضع BOT_TOKEN في متغيرات البيئة قبل التشغيل.")
    threading.Thread(target=poll, daemon=True).start()
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

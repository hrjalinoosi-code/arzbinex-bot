import requests
from datetime import datetime
import sys

# ================== تنظیمات ==================
BALE_BOT_TOKEN = "1775052708:4gUpxaLWAyN44nghGe7kp9zNCyk7jX5nt2g"
BALE_CHANNEL_ID = "@arzbinex"

TELEGRAM_BOT_TOKEN = "8889231097:AAHtdGUmNjJO_-YRG_UIT9-96mM_7f-cu14"
TELEGRAM_CHANNEL_ID = "@arzbinextelegram"

API_LIVE = "https://nerkh.jahankhahan.shop/data/live.json"
API_ARCHIVE = "https://nerkh.jahankhahan.shop/data/rates.json"
# ============================================

def is_friday_in_iran():
    """بررسی اینکه آیا امروز جمعه است یا خیر"""
    return datetime.now().weekday() == 4

def to_persian_digits(text):
    text = str(text)
    translation_table = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return text.translate(translation_table)

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def get_jalali_date_str():
    """فقط تاریخ شمسی را برمی‌گرداند (بدون ساعت)"""
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    date_str = f"{jy}/{jm:02d}/{jd:02d}"
    return f"🕐 تاریخ به‌روزرسانی: {to_persian_digits(date_str)}"

def fetch_json(url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"خطا در دریافت {url}: {e}")
        return None

def get_yesterday_rate(archive_data, series_key):
    if not archive_data or "series" not in archive_data:
        return None
    for series in archive_data["series"]:
        if series["key"] == series_key:
            days = series.get("days", [])
            if not days:
                return None
            now = datetime.now()
            jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
            today_str = f"{jy}/{jm:02d}/{jd:02d}"
            for date_str, rate in reversed(days):
                if date_str < today_str:
                    return rate
    return None

def calc_change_percent(current, previous):
    if previous is None or previous == 0:
        return ""
    change = ((current - previous) / previous) * 100
    if change > 0:
        return f"🟢 ٪{to_persian_digits(f'{change:.2f}')}+"
    elif change < 0:
        return f"🔴 ٪{to_persian_digits(f'{abs(change):.2f}')}-"
    else:
        return "⚪ ٪۰"

def format_row(emoji, label, current_value, previous_value, unit="", force_english=False):
    if force_english:
        val_str = f"{current_value:,}" if isinstance(current_value, (int, float)) else str(current_value)
    else:
        val_str = to_persian_digits(f"{current_value:,}") if isinstance(current_value, (int, float)) else to_persian_digits(str(current_value))
    if unit:
        val_str += f" {unit}"
    title = f"{emoji} {label}:"
    line = f"{title}   {val_str}"
    change_str = calc_change_percent(current_value, previous_value)
    if change_str:
        line += f"   {change_str}"
    return line

def format_message():
    live_data = fetch_json(API_LIVE)
    if not live_data:
        return "❌ متأسفانه در دریافت قیمت‌های لحظه‌ای خطایی رخ داد."
    archive_data = fetch_json(API_ARCHIVE)
    rates = live_data.get("rates", {})
    usd_data = live_data.get("usd", {})
    def get_live(key): return rates.get(key, 0)
    
    rows = []
    # ارزها
    rows.append(format_row('🇺🇸', 'دلار', get_live('dollar'), get_yesterday_rate(archive_data, 'dollar')))
    rows.append(format_row('🇪🇺', 'یورو', get_live('euro'), get_yesterday_rate(archive_data, 'euro')))
    rows.append(format_row('🇬🇧', 'پوند انگلیس', get_live('pound'), get_yesterday_rate(archive_data, 'pound')))
    rows.append(format_row('🇹🇷', 'لیر ترکیه', get_live('lira'), get_yesterday_rate(archive_data, 'lira')))
    rows.append(format_row('🇨🇳', 'یوان چین', get_live('yuan'), get_yesterday_rate(archive_data, 'yuan')))
    rows.append(format_row('🇨🇦', 'دلار کانادا', get_live('cad'), get_yesterday_rate(archive_data, 'cad')))
    rows.append(format_row('🇦🇺', 'دلار استرالیا', get_live('aud'), get_yesterday_rate(archive_data, 'aud')))
    rows.append(format_row('🇮🇶', 'دینار عراق', get_live('iqd'), get_yesterday_rate(archive_data, 'iqd')))
    rows.append(format_row('🇷🇺', 'روبل روسیه', get_live('rub'), get_yesterday_rate(archive_data, 'rub')))
    rows.append(format_row('🇦🇪', 'درهم امارات', get_live('aed'), get_yesterday_rate(archive_data, 'aed')))
    rows.append(format_row('🇨🇭', 'فرانک سوئیس', get_live('chf'), get_yesterday_rate(archive_data, 'chf')))
    rows.append(format_row('🇸🇦', 'ریال سعودی', get_live('sar'), get_yesterday_rate(archive_data, 'sar')))
    rows.append(format_row('🇶🇦', 'ریال قطر', get_live('qar'), get_yesterday_rate(archive_data, 'qar')))
    rows.append(format_row('🇰🇼', 'دینار کویت', get_live('kwd'), get_yesterday_rate(archive_data, 'kwd')))
    rows.append(format_row('🇴🇲', 'ریال عمان', get_live('omr'), get_yesterday_rate(archive_data, 'omr')))
    rows.append("➖➖➖➖➖➖➖➖➖➖")
    
    # طلا
    rows.append(format_row('🟡', 'مثقال طلا', get_live('mesghal'), get_yesterday_rate(archive_data, 'mesghal')))
    rows.append(format_row('🟡', 'طلای ۱۸ عیار', get_live('gold'), get_yesterday_rate(archive_data, 'gold')))
    rows.append(format_row('🟡', 'طلای ۲۴ عیار', get_live('gold24'), get_yesterday_rate(archive_data, 'gold24')))
    rows.append("")
    
    # سکه
    rows.append(format_row('🟠', 'سکه امامی', get_live('coin'), get_yesterday_rate(archive_data, 'coin')))
    rows.append(format_row('🟠', 'سکه بهار آزادی', get_live('bahar'), get_yesterday_rate(archive_data, 'bahar')))
    rows.append(format_row('🟠', 'نیم سکه', get_live('half'), get_yesterday_rate(archive_data, 'half')))
    rows.append(format_row('🟠', 'ربع سکه', get_live('quarter'), get_yesterday_rate(archive_data, 'quarter')))
    rows.append(format_row('🟠', 'سکه گرمی', get_live('gram'), get_yesterday_rate(archive_data, 'gram')))
    rows.append("")
    
    # نقره
    rows.append(format_row('⚪️', 'نقره', get_live('silver'), get_yesterday_rate(archive_data, 'silver')))
    rows.append("➖➖➖➖➖➖➖➖➖➖")
    
    # دیجیتال
    rows.append(format_row('🟣', 'تتر', get_live('tether'), get_yesterday_rate(archive_data, 'tether')))
    rows.append(format_row('🟣', 'بیت‌کوین', get_live('bitcoin'), get_yesterday_rate(archive_data, 'bitcoin')))
    rows.append("")
    
    # انس
    ounce = usd_data.get("ounce", 0)
    silver_ounce = usd_data.get("silver-ounce", 0)
    rows.append(format_row('⚪️', 'انس طلا', ounce, None, '$', force_english=True))
    rows.append(format_row('⚪️', 'انس نقره', silver_ounce, None, '$', force_english=True))

    header = get_jalali_date_str()
    body = "\n".join(rows)
    footer = """
💰💰 نرخ لحظه‌ای بازارها در "ارزبینکس" 💰💰
[بله](https://ble.ir/arzbinex) | [تلگرام](https://t.me/arzbinextelegram)"""
    return f"{header}\n\n{body}\n{footer}"

def send_to_messengers(text):
    # بله
    bale_url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    bale_payload = {"chat_id": BALE_CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(bale_url, json=bale_payload, timeout=20)
        print("✅ بله" if r.status_code == 200 else f"❌ خطا بله: {r.status_code}")
    except Exception as e: print(f"❌ بله: {e}")

    # تلگرام
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    tg_payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(tg_url, json=tg_payload, timeout=20)
        print("✅ تلگرام" if r.status_code == 200 else f"❌ خطا تلگرام: {r.status_code}")
    except Exception as e: print(f"❌ تلگرام: {e}")

if __name__ == "__main__":
    if is_friday_in_iran():
        print("امروز جمعه است. اجرا متوقف شد.")
        sys.exit(0)
    print("در حال دریافت و ارسال...")
    text = format_message()
    send_to_messengers(text)

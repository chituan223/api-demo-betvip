from flask import Flask, jsonify
import requests, time, threading, os
from collections import deque

app = Flask(__name__)

# ================== CẤU HÌNH ==================
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
DATA_FILE = "thuattoan_taixiu.txt"

# ================== BỘ NHỚ ==================
history = deque(maxlen=1000)
last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "---",
    "do_tin_cay": 0,
    "cau": "",
    "id": "lc79"
}

# ================== LẤY DỮ LIỆU THẬT ==================
def get_taixiu_data():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json().get("list", [])
        if not data:
            return None

        newest = data[0]
        phien = newest.get("id")
        dice = newest.get("dices", [1, 2, 3])
        tong = newest.get("point", sum(dice))

        raw = newest.get("resultTruyenThong", "").upper()
        if raw == "TAI":
            ketqua = "Tài"
        elif raw == "XIU":
            ketqua = "Xỉu"
        else:
            ketqua = "Tài" if tong >= 11 else "Xỉu"

        return phien, dice, tong, ketqua

    except Exception as e:
        print("❌ API lỗi:", e)
        return None

# ================== TÍNH XÁC SUẤT 10 PHIÊN ==================
def tinh_xac_suat_10():
    last10 = list(history)[-10:]
    if len(last10) < 10:
        return "---", 0, ""

    tai = last10.count("Tài")
    xiu = last10.count("Xỉu")

    if tai >= xiu:
        return "Tài", round(tai / 10 * 100), "".join("T" if x == "Tài" else "X" for x in last10)
    else:
        return "Xỉu", round(xiu / 10 * 100), "".join("T" if x == "Tài" else "X" for x in last10)

# ================== LƯU FILE THUẬT TOÁN ==================
def save_to_file(cau, tai_pct, xiu_pct):
    if not os.path.exists(DATA_FILE):
        open(DATA_FILE, "w", encoding="utf-8").close()

    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{cau} | TAI={tai_pct}% | XIU={xiu_pct}%\n")

# ================== THREAD CHẠY NGẦM ==================
def background_updater():
    global last_data
    last_phien = None

    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data

            if phien != last_phien:
                history.append(ketqua)

                du_doan, do_tin_cay, cau = tinh_xac_suat_10()

                if do_tin_cay > 0:
                    save_to_file(cau, 
                                 do_tin_cay if du_doan == "Tài" else 100 - do_tin_cay,
                                 do_tin_cay if du_doan == "Xỉu" else 100 - do_tin_cay)

                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": du_doan,
                    "do_tin_cay": do_tin_cay,
                    "cau": cau,
                    "id": "lc79"
                }

                print(f"✅ Phiên {phien} | {ketqua} | {tong}")
                last_phien = phien

        time.sleep(5)

# ================== API ==================
@app.route("/api/taixiu")
def api_taixiu():
    return jsonify(last_data)

@app.route("/")
def home():
    return "LC79 API RUNNING"

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Server đang chạy...")
    threading.Thread(target=background_updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

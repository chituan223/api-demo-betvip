from flask import Flask, jsonify
import requests, time, threading, os
from collections import deque

app = Flask(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
DATA_FILE = "thuattoan_taixiu.txt"

history = deque(maxlen=200)

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "trang_thai_cau": "CHỜ",
    "khuyen_nghi": "không vào",
    "xac_suat_tai": 0,
    "xac_suat_xiu": 0,
      "cau": "",
}

# ================== API THẬT ==================
def get_data():
    try:
        r = requests.get(API_URL, timeout=10)
        data = r.json().get("list", [])
        if not data:
            return None

        n = data[0]
        phien = n["id"]
        d = n["dices"]
        tong = n["point"]
        raw = n.get("resultTruyenThong", "").upper()

        if raw == "TAI":
            kq = "Tài"
        elif raw == "XIU":
            kq = "Xỉu"
        else:
            kq = "Tài" if tong >= 11 else "Xỉu"

        return phien, d, tong, kq
    except:
        return None

# ================== PHÂN TÍCH CẦU ==================
def phan_tich():
    last20 = list(history)[-20:]
    if len(last20) < 20:
        return "CHƯA ĐỦ DỮ LIỆU", "không vào", 0, 0, ""

    tai = last20.count("Tài")
    xiu = last20.count("Xỉu")

    pt_tai = round(tai / 20 * 100)
    pt_xiu = round(xiu / 20 * 100)

    cau = "".join("T" if x == "Tài" else "X" for x in last20)

    # Đếm bệt
    bet_len = 1
    for i in range(len(last20)-1, 0, -1):
        if last20[i] == last20[i-1]:
            bet_len += 1
        else:
            break

    # Đếm đảo
    dao = sum(1 for i in range(1, len(last20)) if last20[i] != last20[i-1])

    # ĐÁNH GIÁ
    if dao >= 12:
        return "CẦU NHIỄU", "KHÔNG NÊN VÀO", pt_tai, pt_xiu, cau

    if bet_len >= 4:
        return "CẦU BỆT", "CÓ THỂ THEO NHỎ", pt_tai, pt_xiu, cau

    if abs(pt_tai - pt_xiu) <= 10:
        return "CẦU XẤU", "NO BET", pt_tai, pt_xiu, cau

    return "CẦU ỔN", "THEO NHỎ – 1 TAY", pt_tai, pt_xiu, cau

# ================== GHI FILE ==================
def save_log():
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{last_data}\n")

# ================== THREAD ==================
def run():
    last_phien = None
    while True:
        d = get_data()
        if d:
            phien, dice, tong, kq = d
            if phien != last_phien:
                history.append(kq)

                trang_thai, khuyen, pt_tai, pt_xiu, cau = phan_tich()

                last_data.update({
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": kq,
                    "trang_thai_cau": trang_thai,
                    "khuyen_nghi": khuyen,
                    "xac_suat_tai": pt_tai,
                    "xac_suat_xiu": pt_xiu,
                    "cau": cau
                })

                save_log()
                print(phien, kq, trang_thai, khuyen)
                last_phien = phien
        time.sleep(5)

# ================== API ==================
@app.route("/api/taixiu")
def api():
    return jsonify(last_data)

@app.route("/")
def home():
    return ""

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

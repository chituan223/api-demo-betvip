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

# ================== TÍNH XÁC SUẤT CHUẨN ==================
def tinh_xac_suat_chuan():
    last10 = list(history)[-15:]
    if len(last10) < 15:
        return "---", 0, ""

    tai = last10.count("Tài")
    xiu = last10.count("Xỉu")

    freq_tai = tai / 10 * 100
    freq_xiu = xiu / 10 * 100

    # Xu hướng 3 phiên cuối
    last3 = last10[-3:]
    trend = last3.count("Tài") / 3 * 100

    # Độ lệch quá mạnh → trừ điểm
    bias_penalty = 0
    if freq_tai >= 80 or freq_xiu >= 80:
        bias_penalty = 10

    # Xác suất tổng hợp
    final_tai = 0.6 * freq_tai + 0.3 * trend - bias_penalty
    final_xiu = 100 - final_tai

    # Giới hạn an toàn
    final_tai = max(55, min(85, round(final_tai)))
    final_xiu = 100 - final_tai

    du_doan = "Tài" if final_tai >= final_xiu else "Xỉu"
    do_tin_cay = max(final_tai, final_xiu)

    cau = "".join("T" if x == "Tài" else "X" for x in last10)

    return du_doan, do_tin_cay, cau

# ================== LƯU FILE ==================
def save_to_file(cau, du_doan, do_tin_cay):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{cau} | DU_DOAN={du_doan} | TIN_CAY={do_tin_cay}%\n")

# ================== THREAD ==================
def background_updater():
    global last_data
    last_phien = None

    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data

            if phien != last_phien:
                history.append(ketqua)

                du_doan, do_tin_cay, cau = tinh_xac_suat_chuan()

                if do_tin_cay > 0:
                    save_to_file(cau, du_doan, do_tin_cay)

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

                print(f"✅ Phiên {phien} | {ketqua} | {du_doan} ({do_tin_cay}%)")
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

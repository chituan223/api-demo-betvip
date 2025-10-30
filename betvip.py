from flask import Flask, jsonify
import requests

app = Flask(__name__)

# =================== CẤU HÌNH ===================
SOURCE_URL = "https://wtx.macminim6.online/v1/tx/sessions?cp=R&cl=R&pf=web&at=729bb3bd25e79dc6b30dbdfc2459b52f"
ID = "tuananhdz"

# =================== THUẬT TOÁN MỚI ===================
def algo_vote_pro(history):
    if len(history) < 8:
        return {"prediction": "Tài", "confidence": 50}

    # -------- Các thuật toán con --------
    def trend_force(h):
        score = sum((i if v == "Tài" else -i) for i, v in enumerate(h[-6:], 1))
        return "Tài" if score >= 0 else "Xỉu"

    def rebound(h):
        if len(h) < 6: return "Tài"
        last4 = h[-4:]
        if last4[-1] != last4[-2] and last4[-3] == last4[-4]:
            return last4[-3]
        return h[-1]

    def cycle(h):
        if len(h) < 8: return "Tài"
        prev, now = h[-6:-3], h[-3:]
        return now[-1] if prev == now else ("Tài" if h[-1] == "Xỉu" else "Xỉu")

    def momentum(h):
        tai = h[-5:].count("Tài")
        return "Tài" if tai >= 3 else "Xỉu"

    def balance(h):
        streaks, streak = [], 1
        for i in range(1, len(h)):
            if h[i] == h[i - 1]:
                streak += 1
            else:
                streaks.append(streak)
                streak = 1
        streaks.append(streak)
        if len(streaks) < 3: return "Tài"
        avg = sum(streaks[-3:]) / 3
        return "Tài" if streaks[-1] >= avg else "Xỉu"

    def stat_bias(h):
        tai = h[-10:].count("Tài")
        xiu = 10 - tai
        if abs(tai - xiu) <= 2:
            return "Tài" if h[-1] == "Xỉu" else "Xỉu"
        return "Tài" if tai > xiu else "Xỉu"

    # -------- Tổng hợp kết quả --------
    algos = [trend_force, rebound, cycle, momentum, balance, stat_bias]
    votes = [a(history) for a in algos]
    tai_votes = votes.count("Tài")
    xiu_votes = votes.count("Xỉu")

    # -------- Kết luận --------
    prediction = "Tài" if tai_votes > xiu_votes else "Xỉu"
    confidence = int((max(tai_votes, xiu_votes) / len(algos)) * 100)

    return {
        "prediction": prediction,
        "confidence": confidence,
        "votes": {
            "Tài": tai_votes,
            "Xỉu": xiu_votes,
            "Chi_tiet": votes
        }
    }

# =================== API CHÍNH ===================
@app.route("/api/taixiumd5", methods=["GET"])
def get_prediction():
    try:
        res = requests.get(SOURCE_URL, timeout=10)
        data = res.json()

        if not data or "list" not in data or len(data["list"]) == 0:
            return jsonify({"error": "Không có dữ liệu hợp lệ"}), 400

        newest = data["list"][0]
        dices = newest.get("dices", [0, 0, 0])
        total = sum(dices)
        phien = newest.get("id", 0)
        result = newest.get("resultTruyenThong", "").upper()

        # Lưu lịch sử
        if not hasattr(app, "history"):
            app.history = []
        if result:
            app.history.append("Tài" if result == "TAI" else "Xỉu")
        if len(app.history) > 100:
            app.history = app.history[-100:]

        # Dự đoán
        prediction_data = algo_vote_pro(app.history)

        return jsonify({
            "Phien": phien,
            "Xuc_xac_1": dices[0],
            "Xuc_xac_2": dices[1],
            "Xuc_xac_3": dices[2],
            "Tong": total,
            "Du_doan": prediction_data["prediction"],
            "Do_tin_cay": prediction_data["confidence"],
            "Id": ID
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
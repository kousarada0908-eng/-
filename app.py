import os
from flask import Flask, render_template

app = Flask(__name__)

# =========================
# トップページ
# =========================
@app.route("/")
def index():
    # もしテンプレート使ってる場合
    return render_template("index.html")

# =========================
# 例：API用（必要なら使う）
# =========================
@app.route("/api/test")
def api_test():
    return {"status": "ok"}

# =========================
# Render対応起動設定
# ★ここが重要
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",   # ← Renderで必須
        port=port,        # ← Renderが指定するポート
        debug=False       # ← 本番はFalse
    )

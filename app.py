from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret"  # ログイン用

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

products = load_data()

# 🔐 ログイン
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["login"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# 📊 メイン
@app.route("/")
def index():
    if not session.get("login"):
        return redirect("/login")

    period = request.args.get("period", "all")

    today = datetime.now()

    names = []
    sales = []

    for p in products:
        total = 0
        for h in p.get("history", []):
            date = datetime.strptime(h["date"], "%Y-%m-%d")

            if period == "1":
                if date >= today - timedelta(days=1):
                    total += 1
            elif period == "3":
                if date >= today - timedelta(days=3):
                    total += 1
            elif period == "7":
                if date >= today - timedelta(days=7):
                    total += 1
            else:
                total += 1

        names.append(p["name"])
        sales.append(total)

    ranking = sorted(
        products,
        key=lambda x: x["price"] * x["sold"],
        reverse=True
    )

    total_sales = sum(p["price"] * p["sold"] for p in products)

    return render_template(
        "index.html",
        products=products,
        total_sales=total_sales,
        names=names,
        sales=sales,
        ranking=ranking,
        period=period
    )

# ➕ 追加
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        stock = int(request.form["stock"])

        file = request.files.get("image")

        filename = ""
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        products.append({
            "name": name,
            "price": price,
            "stock": stock,
            "sold": 0,
            "image": filename,
            "history": []
        })

        save_data()
        return redirect("/")

    return render_template("add.html")

# 💰 売る
@app.route("/sell/<int:id>")
def sell(id):
    if products[id]["stock"] > 0:
        products[id]["stock"] -= 1
        products[id]["sold"] += 1

        products[id]["history"].append({
            "date": datetime.now().strftime("%Y-%m-%d")
        })

        save_data()

    return redirect("/")

# 🗑 削除
@app.route("/delete/<int:id>")
def delete(id):
    if 0 <= id < len(products):
        products.pop(id)
        save_data()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

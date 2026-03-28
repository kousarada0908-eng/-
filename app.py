import os
import json
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"

DB = "app.db"

# ===== メール送信 =====
def send_mail(to_email, message):
    msg = MIMEText(message)
    msg["Subject"] = "売上通知"
    msg["From"] = to_email
    msg["To"] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(to_email, session.get("email_pass"))  # ←注意
    server.send_message(msg)
    server.quit()

# ===== DB =====
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        email_pass TEXT,
        notify_type TEXT DEFAULT 'all'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        stock INTEGER,
        images TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ===== ホーム =====
@app.route("/")
def index():
    conn = get_db()

    products = conn.execute("SELECT * FROM products").fetchall()

    table_data = []
    for p in products:
        sold = conn.execute(
            "SELECT COUNT(*) FROM sales WHERE product_id=?",
            (p["id"],)
        ).fetchone()[0]

        table_data.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "stock": p["stock"],
            "total": sold * p["price"],
            "images": json.loads(p["images"]) if p["images"] else []
        })

    return render_template("index.html", table_data=table_data)

# ===== ユーザー登録 =====
@app.route("/register", methods=["POST"])
def register():
    conn = get_db()
    conn.execute(
        "INSERT INTO users (email, email_pass) VALUES (?, ?)",
        (request.form["email"], request.form["email_pass"])
    )
    conn.commit()
    return redirect("/")

# ===== 売る =====
@app.route("/sell/<int:id>")
def sell(id):
    conn = get_db()

    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()

    conn.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (id,))
    conn.execute(
        "INSERT INTO sales (product_id, date) VALUES (?, ?)",
        (id, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()

    # ユーザー取得
    user = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1").fetchone()

    if user and user["notify_type"] != "none":
        send_mail(user["email"], f"{product['name']} が売れました！")

    return "", 204

# ===== 通知設定 =====
@app.route("/set_notify", methods=["POST"])
def set_notify():
    conn = get_db()
    conn.execute(
        "UPDATE users SET notify_type=? ORDER BY id DESC LIMIT 1",
        (request.form["notify_type"],)
    )
    conn.commit()
    return redirect("/")

# ===== 商品追加 =====
@app.route("/add", methods=["POST"])
def add():
    files = request.files.getlist("images")

    paths = []
    for f in files[:5]:
        if f.filename:
            path = os.path.join("static/uploads", f.filename)
            f.save(path)
            paths.append(path)

    conn = get_db()
    conn.execute(
        "INSERT INTO products (name, price, stock, images) VALUES (?, ?, ?, ?)",
        (
            request.form["name"],
            int(request.form["price"]),
            int(request.form["stock"]),
            json.dumps(paths)
        )
    )
    conn.commit()

    return redirect("/")

# ===== 削除 =====
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

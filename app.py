import os
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"

DB = "app.db"

# =========================
# DB接続
# =========================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# DB初期化
# =========================
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        price INTEGER,
        stock INTEGER
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

# =========================
# 🔐 ログイン
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/")

    return render_template("login.html")

# =========================
# 🏠 メイン画面
# =========================
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    names = []
    sold_data = []
    unsold_data = []
    table_data = []
    total_sum = 0

    for p in products:
        sold = conn.execute(
            "SELECT COUNT(*) FROM sales WHERE product_id=?",
            (p["id"],)
        ).fetchone()[0]

        unsold = p["stock"]
        total = sold * p["price"]

        names.append(p["name"])
        sold_data.append(sold)
        unsold_data.append(unsold)
        total_sum += total

        table_data.append({
            "name": p["name"],
            "price": p["price"],
            "sold": sold,
            "unsold": unsold,
            "total": total
        })

    # 📊 日別売上
    daily = conn.execute("""
        SELECT date, SUM(products.price) as total
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY date
        ORDER BY date
    """).fetchall()

    dates = [d["date"] for d in daily]
    daily_sales = [d["total"] for d in daily]

    return render_template(
        "index.html",
        names=names,
        sold_data=sold_data,
        unsold_data=unsold_data,
        table_data=table_data,
        total_sum=total_sum,
        dates=dates,
        daily_sales=daily_sales
    )

# =========================
# ➕ 商品追加
# =========================
@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    conn.execute(
        "INSERT INTO products (user_id, name, price, stock) VALUES (?, ?, ?, ?)",
        (session["user_id"], request.form["name"], request.form["price"], request.form["stock"])
    )
    conn.commit()
    return redirect("/")

# =========================
# 💰 売る
# =========================
@app.route("/sell/<int:id>")
def sell(id):
    conn = get_db()
    conn.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (id,))
    conn.execute(
        "INSERT INTO sales (product_id, date) VALUES (?, ?)",
        (id, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    return redirect("/")

# =========================
# 🗑 削除
# =========================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

# =========================
# 🚀 Render対応 起動設定（ここが重要）
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",   # ← Render必須
        port=port,
        debug=False       # ← 本番はFalse
    )

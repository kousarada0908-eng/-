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
# ログイン
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
# 新規登録
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (request.form["username"], request.form["password"])
        )
        conn.commit()
        return redirect("/login")

    return render_template("register.html")

# =========================
# メイン（グラフ対応）
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

    table_data = []
    names = []
    sold_counts = []
    total_sum = 0

    for p in products:
        sold = conn.execute(
            "SELECT COUNT(*) FROM sales WHERE product_id=?",
            (p["id"],)
        ).fetchone()[0]

        total = sold * p["price"]
        total_sum += total

        table_data.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "stock": p["stock"],
            "sold": sold,
            "total": total
        })

        names.append(p["name"])
        sold_counts.append(sold)

    # 日別売上
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
        table_data=table_data,
        names=names,
        sold_counts=sold_counts,
        dates=dates,
        daily_sales=daily_sales,
        total_sum=total_sum
    )

# =========================
# 商品追加
# =========================
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    price = int(request.form["price"])
    stock = int(request.form["stock"])

    conn = get_db()
    conn.execute(
        "INSERT INTO products (user_id, name, price, stock) VALUES (?, ?, ?, ?)",
        (session["user_id"], name, price, stock)
    )
    conn.commit()

    return redirect("/")

# =========================
# 売る
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
# 削除
# =========================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

# =========================
# Render対応
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"
DB = "app.db"


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
        username TEXT,
        password TEXT,
        email TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        price INTEGER,
        stock INTEGER,
        image TEXT
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


# =====================
# ログイン
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form.get("username"), request.form.get("password"))
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            flash("ログイン失敗")

    return render_template("login/login.html")


# =====================
# 登録
# =====================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (
                request.form.get("username"),
                request.form.get("password"),
                request.form.get("email")
            )
        )
        conn.commit()
        return redirect("/login")

    return render_template("login/register.html")


# =====================
# ダッシュボード
# =====================
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
            "total": total,
            "image": p["image"]
        })

        names.append(p["name"])
        sold_counts.append(sold)

    pie_labels = names
    pie_data = sold_counts

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
        total_sum=total_sum,
        dates=dates,
        daily_sales=daily_sales,
        pie_labels=pie_labels,
        pie_data=pie_data
    )


# =====================
# 商品追加
# =====================
@app.route("/add", methods=["POST"])
def add():
    conn = get_db()
    conn.execute(
        "INSERT INTO products (user_id, name, price, stock, image) VALUES (?, ?, ?, ?, ?)",
        (
            session["user_id"],
            request.form.get("name"),
            int(request.form.get("price")),
            int(request.form.get("stock")),
            request.form.get("image")
        )
    )
    conn.commit()
    return redirect("/")


# =====================
# 売る
# =====================
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


# =====================
# 削除
# =====================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return redirect("/")


# =====================
# ログアウト
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)

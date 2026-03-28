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
# 初期化
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
# 登録
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
# メイン
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
    total_stock = 0

    for p in products:
        sold = conn.execute(
            "SELECT COUNT(*) FROM sales WHERE product_id=?",
            (p["id"],)
        ).fetchone()[0]

        total = sold * p["price"]
        total_sum += total
        total_stock += p["stock"]

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

    # =========================
    # 円グラフ
    # =========================
    pie_labels = names + ["売れ残り"]
    pie_data = sold_counts + [total_stock]

    # =========================
    # 集計モード（日 / 週 / 月）
    # =========================
    mode = request.args.get("mode", "day")

    if mode == "month":
        date_format = "%Y-%m"
    elif mode == "week":
        date_format = "%Y-%W"
    else:
        date_format = "%Y-%m-%d"

    # =========================
    # 合計グラフ
    # =========================
    daily = conn.execute(f"""
        SELECT strftime('{date_format}', date) as d, SUM(products.price) as total
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY d
        ORDER BY d
    """).fetchall()

    dates = [d["d"] for d in daily]
    daily_sales = [d["total"] for d in daily]

    # =========================
    # 商品別グラフ（DBから生成）
    # =========================
    product_sales = conn.execute(f"""
        SELECT products.name, strftime('{date_format}', sales.date) as d, SUM(products.price) as total
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY products.name, d
        ORDER BY d
    """).fetchall()

    product_daily = {}

    for row in product_sales:
        name = row["name"]
        d = row["d"]
        total = row["total"]

        if name not in product_daily:
            product_daily[name] = {}

        product_daily[name][d] = total

    # 日付に合わせて整形
    for name in product_daily:
        product_daily[name] = [
            product_daily[name].get(d, 0) for d in dates
        ]

    return render_template(
        "index.html",
        table_data=table_data,
        total_sum=total_sum,
        dates=dates,
        daily_sales=daily_sales,
        product_daily=product_daily,
        pie_labels=pie_labels,
        pie_data=pie_data
    )

# =========================
# 商品追加
# =========================
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute(
        "INSERT INTO products (user_id, name, price, stock) VALUES (?, ?, ?, ?)",
        (session["user_id"], request.form["name"], int(request.form["price"]), int(request.form["stock"]))
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
# CSVダウンロード
# =========================
@app.route("/download")
def download():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    data = conn.execute("""
        SELECT products.name, sales.date, products.price
        FROM sales
        JOIN products ON sales.product_id = products.id
    """).fetchall()

    csv_data = "商品名,日付,価格\n"
    for row in data:
        csv_data += f"{row['name']},{row['date']},{row['price']}\n"

    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=sales.csv"
    }

# =========================
# 起動
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

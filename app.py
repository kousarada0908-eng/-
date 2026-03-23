from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# デザイン
design = "simple"

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

@app.route("/")
def index():
    total_sales = sum(p["price"] * p["sold"] for p in products)
    return render_template(
        "index.html",
        products=products,
        total_sales=total_sales,
        design=design  
    )

# デザイン切り替え
@app.route("/change_design/<mode>")
def change_design(mode):
    global design
    design = mode
    return redirect("/")

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
            "image": filename
        })

        save_data()
        return redirect("/")

    return render_template("add.html")



@app.route("/sell/<int:id>")
def sell(id):
    if products[id]["stock"] > 0:
        products[id]["stock"] -= 1
        products[id]["sold"] += 1
        save_data()
        
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

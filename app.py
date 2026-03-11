from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "foodbudget"


# FOOD MENU DATA (Dynamic Images)
foods = [
{"id":1,"name":"Chicken Biryani","price":180,"image":"chicken_biryani.jpg"},
{"id":2,"name":"Pizza","price":200,"image":"pizza.jpg"},
{"id":3,"name":"Dosa","price":80,"image":"dosa.jpg"},
{"id":4,"name":"Noodles","price":120,"image":"noodles.jpg"},
{"id":5,"name":"Burger","price":150,"image":"burger.jpg"},
{"id":6,"name":"Fried Rice","price":140,"image":"fried_rice.jpg"},
{"id":7,"name":"Sandwich","price":90,"image":"sandwich.jpg"},
{"id":8,"name":"Ice Cream","price":70,"image":"ice_cream.jpg"}
]
# DATABASE
def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        budget INTEGER,
        spent INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()


# LOGIN PAGE
@app.route("/")
def login():
    return render_template("login.html")


# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO users (name,email,password,budget,spent) VALUES (?,?,?,?,?)",
            (name,email,password,0,0)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# LOGIN CHECK
@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password)
    )

    user = c.fetchone()

    conn.close()

    if user:

        session["user_id"] = user[0]
        session["name"] = user[1]

        return redirect("/budget")

    return "Invalid Login"


# SET BUDGET
@app.route("/budget", methods=["GET","POST"])
def budget():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        budget = request.form["budget"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "UPDATE users SET budget=? WHERE id=?",
            (budget,session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect("/home")

    return render_template("budget.html")


# HOME PAGE
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT budget,spent FROM users WHERE id=?",
        (session["user_id"],)
    )

    data = c.fetchone()
    conn.close()

    budget = data[0]
    spent = data[1]
    remaining = budget - spent

    return render_template(
        "home.html",
        name=session["name"],
        budget=budget,
        spent=spent,
        remaining=remaining,
        foods=foods
    )


# SEARCH PAGE
@app.route("/search")
def search():
    query = request.args.get("q")

    if query:
        results = [f for f in foods if query.lower() in f["name"].lower()]
    else:
        results = foods

    return render_template("search.html", foods=results)
    


# ADD TO CART
@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(id)
    session.modified = True

    return redirect("/cart")


# CART PAGE
@app.route("/cart")
def cart():

    cart_items = []

    if "cart" in session:

        for item in session["cart"]:
            for food in foods:
                if food["id"] == item:
                    cart_items.append(food)

    total = sum(item["price"] for item in cart_items)

    return render_template(
        "cart.html",
        items=cart_items,
        total=total
    )


# PLACE ORDER
@app.route("/place_order")
def place_order():

    cart_items = []

    if "cart" in session:

        for item in session["cart"]:
            for food in foods:
                if food["id"] == item:
                    cart_items.append(food)

    total = sum(item["price"] for item in cart_items)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "UPDATE users SET spent = spent + ? WHERE id=?",
        (total, session["user_id"])
    )

    conn.commit()
    conn.close()

    session["cart"] = []

    return redirect("/home")


if __name__ == "__main__":
    app.run(debug=True)

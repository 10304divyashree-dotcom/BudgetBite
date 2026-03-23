from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "foodbudget"


foods = [
{"id":1,"name":"Chicken Briyani","price":180,"image":"chicken_biryani.jpg","category":"biryani"},
{"id":2,"name":"Mutton Briyani","price":200,"image":"mutton_briyani.jpg","category":"biryani"},
{"id":3,"name":"Pizza","price":200,"image":"pizza.jpg","category":"pizza"},
{"id":4,"name":"Dosa","price":80,"image":"dosa.jpg","category":"south"},
{"id":5,"name":"Noodles","price":120,"image":"noodles.jpg","category":"chinese"},
{"id":6,"name":"Fried Rice","price":120,"image":"fried_rice.jpg","category":"chinese"},
{"id":7,"name":"Chicken Fried Rice","price":150,"image":"chickenfriedrice.jpg","category":"chinese"},
{"id":8,"name":"Sandwich","price":90,"image":"sandwich.jpg","category":"fastfood"},
{"id":9,"name":"Burger","price":150,"image":"burger.jpg","category":"fastfood"},
{"id":10,"name":"Vanilla Ice Cream","price":50,"image":"ice_cream.jpg","category":"dessert"},
{"id":11,"name":"Chocolate Ice Cream","price":70,"image":"chocolate_icecream.jpg","category":"dessert"},
{"id":12,"name":"Butter Scotch Ice Cream","price":70,"image":"butterscotch_icecream.jpg","category":"dessert"}
]


# DATABASE
def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        budget INTEGER,
        spent INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT,
        price INTEGER,
        order_time TEXT
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

    cart_count = len(session.get("cart", []))

    return render_template(
        "home.html",
        name=session["name"],
        budget=budget,
        spent=spent,
        remaining=remaining,
        foods=foods,
        cart_count=cart_count
    )


# SEARCH
@app.route("/search")
def search():

    query = request.args.get("q")

    if query:
        results = [f for f in foods if query.lower() in f["name"].lower()]
    else:
        results = foods

    return render_template("search.html", foods=results)

# Category
@app.route("/category/<cat>")
def category(cat):

    category_foods = []

    for food in foods:
        if food["category"] == cat:
            category_foods.append(food)

    return render_template(
        "category.html",
        foods=category_foods,
        category=cat
    )


# ADD TO CART
@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(id)
    session.modified = True

    return redirect("/cart")

@app.route("/remove/<int:id>")
def remove(id):

    if "cart" in session:
        cart = session["cart"]

        if id in cart:
            cart.remove(id)

        session["cart"] = cart
        session.modified = True

    return redirect("/cart")

@app.route("/buy_now/<int:id>")
def buy_now(id):

    if "user_id" not in session:
        return redirect("/")

    # Find selected food
    selected_food = None
    for food in foods:
        if food["id"] == id:
            selected_food = food
            break

    if not selected_food:
        return redirect("/home")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get budget + spent
    c.execute(
        "SELECT budget, spent FROM users WHERE id=?",
        (session["user_id"],)
    )

    data = c.fetchone()
    budget = data[0]
    spent = data[1]

    # Check budget
    if spent + selected_food["price"] > budget:
        conn.close()
        flash("⚠️ Not enough budget!", "danger")
        return redirect("/home")

    # Insert order
    c.execute(
        "INSERT INTO orders (user_id, food_name, price, order_time) VALUES (?,?,?,?)",
        (
            session["user_id"],
            selected_food["name"],
            selected_food["price"],
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    # Update spent
    c.execute(
        "UPDATE users SET spent = spent + ? WHERE id=?",
        (selected_food["price"], session["user_id"])
    )

    conn.commit()
    conn.close()

    flash("✅ Order placed instantly!", "success")

    return redirect("/orders")
# CART PAGE
@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect("/")

    cart_items = []

    if "cart" in session:

        for item in session["cart"]:
            for food in foods:
                if food["id"] == item:
                    cart_items.append(food)

    total = sum(item["price"] for item in cart_items)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# PLACE ORDER
@app.route("/place_order")
def place_order():

    if "user_id" not in session:
        return redirect("/")

    cart_items = []

    if "cart" in session:
        for item in session["cart"]:
            for food in foods:
                if food["id"] == item:
                    cart_items.append(food)

    total = sum(item["price"] for item in cart_items)
    if total == 0:
     flash("🛒 Your cart is empty!", "danger")
     return redirect("/cart")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT budget, spent FROM users WHERE id=?",
        (session["user_id"],)
    )

    data = c.fetchone()

    budget = data[0]
    spent = data[1]

    if spent + total > budget:
        conn.close()
        flash("⚠️ Order exceeds your budget! Please remove some items.", "danger")
        return redirect("/cart")

    # SAVE ORDERS
    for item in cart_items:
        c.execute(
            "INSERT INTO orders (user_id, food_name, price, order_time) VALUES (?,?,?,?)",
            (
                session["user_id"],
                item["name"],
                item["price"],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )

    # UPDATE SPENT
    c.execute(
        "UPDATE users SET spent = spent + ? WHERE id=?",
        (total, session["user_id"])
    )

    conn.commit()
    conn.close()

    session["cart"] = []

    flash("✅ Order placed successfully!", "success")

    return redirect("/orders")


# ORDER HISTORY
@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT food_name, price, order_time FROM orders WHERE user_id=? ORDER BY order_time DESC",
        (session["user_id"],)
    )

    order_list = c.fetchall()

    conn.close()

    return render_template("orders.html", orders=order_list)


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

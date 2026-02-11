import pandas as pd
import io
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from models import db, User, Order, OrderItem
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)

# ---------------- TRANSLATIONS ----------------
translations = {

    "dashboard": {"en": "Production Dashboard", "hi": "उत्पादन डैशबोर्ड"},
    "sales_dashboard": {"en": "Sales Dashboard", "hi": "सेल्स डैशबोर्ड"},

    "total_orders": {"en": "Total Orders", "hi": "कुल ऑर्डर"},
    "pending_orders": {"en": "Pending Orders", "hi": "लंबित ऑर्डर"},
    "completed_orders": {"en": "Completed Orders", "hi": "पूर्ण ऑर्डर"},
    "urgent_orders": {"en": "Urgent Orders", "hi": "जरूरी ऑर्डर"},

    "order_number": {"en": "Order Number", "hi": "ऑर्डर नंबर"},
    "status": {"en": "Status", "hi": "स्थिति"},
    "action": {"en": "Action", "hi": "कार्य"},

    "search_placeholder": {"en": "Search Order or Customer", "hi": "ऑर्डर या ग्राहक खोजें"},

    "view_details": {"en": "View Details", "hi": "विवरण देखें"},
    "mark_completed": {"en": "Mark Completed", "hi": "पूर्ण करें"},
    "logout": {"en": "Logout", "hi": "लॉगआउट"},
    "create_order": {"en": "Create Order", "hi": "ऑर्डर बनाएं"},
    "edit": {"en": "Edit", "hi": "संपादित करें"},
    "update_order": {"en": "Update Order", "hi": "ऑर्डर अपडेट करें"},
    "save_order": {"en": "Save Order", "hi": "ऑर्डर सहेजें"},
    "add_product": {"en": "Add Another Product", "hi": "एक और उत्पाद जोड़ें"},

    "customer_name": {"en": "Customer Name", "hi": "ग्राहक नाम"},
    "place_supply": {"en": "Place of Supply", "hi": "आपूर्ति स्थान"},
    "dispatch_date": {"en": "Dispatch Date", "hi": "डिस्पैच तिथि"},
    "delivery_time": {"en": "Delivery Time", "hi": "डिलीवरी समय"},

    "products": {"en": "Products", "hi": "उत्पाद"},
    "product_name": {"en": "Product Name", "hi": "उत्पाद नाम"},
    "product_code": {"en": "Product Code", "hi": "उत्पाद कोड"},
    "quantity": {"en": "Quantity", "hi": "मात्रा"},
    "revoke_completion": {"en": "Revoke Completion", "hi": "पूर्णता हटाएं"},

}


# ---------------- AUTO DELETE OLD COMPLETED ORDERS ----------------
def delete_old_completed_orders():

    three_days_ago = datetime.now() - timedelta(days=3)

    old_orders = Order.query.filter(
        Order.status == "Completed",
        Order.completed_time <= three_days_ago
    ).all()

    for order in old_orders:

        # Delete related products first
        OrderItem.query.filter_by(order_id=order.id).delete()

        db.session.delete(order)

    db.session.commit()

# ---------------- GLOBAL TRANSLATION ----------------
@app.context_processor
def inject_translations():
    lang = session.get("lang", "en")
    return dict(translations=translations, lang=lang)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- LANGUAGE ROUTE ----------------
@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in ["en", "hi"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("login"))

# ---------------- URGENCY COLOR FUNCTION ----------------
def get_order_color(dispatch_date):

    today = datetime.today().date()
    diff = (dispatch_date - today).days

    if diff <= 3:
        return "red"

    elif 4 <= diff <= 6:
        return "yellow"

    else:
        return "green"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            # ----- ROLE BASED REDIRECT -----
            if user.role == "sales":
                return redirect(url_for("sales_dashboard"))

            elif user.role == "production":
                return redirect(url_for("production_dashboard"))

            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))

        # Optional: you can add error message later

    return render_template("login.html")

# ---------------- SALES DASHBOARD ----------------
@app.route("/sales")
@login_required

def sales_dashboard():
    delete_old_completed_orders()
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template("sales_dashboard.html", orders=orders)

# ---------------- CREATE ORDER ----------------
@app.route("/create_order", methods=["GET", "POST"])
@login_required
def create_order():

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        place_of_supply = request.form["place_of_supply"]
        dispatch_date = request.form["dispatch_date"]

        product_names = request.form.getlist("product_name[]")
        product_codes = request.form.getlist("product_code[]")
        quantities = request.form.getlist("quantity[]")

        order_number = f"ORD{Order.query.count()+1:03}"

        new_order = Order(
    order_number=order_number,
    customer_name=customer_name,
    place_of_supply=place_of_supply,
    order_date=datetime.today(),
    dispatch_date=datetime.strptime(dispatch_date, "%Y-%m-%d"),
    sales_person=current_user.username
)

        db.session.add(new_order)
        db.session.commit()

        for i in range(len(product_names)):
            db.session.add(OrderItem(
                order_id=new_order.id,
                product_name=product_names[i],
                product_code=product_codes[i],
                quantity=quantities[i]
            ))

        db.session.commit()
        return redirect(url_for("sales_dashboard"))

    return render_template("create_order.html")

# ---------------- EDIT ORDER ----------------
@app.route("/edit_order/<int:order_id>", methods=["GET", "POST"])
@login_required
def edit_order(order_id):

    order = Order.query.get(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()

    # SALES SECURITY
    if current_user.role == "sales" and order.sales_person != current_user.username:
        return "❌ You can edit only your own orders"

    if request.method == "POST":

        order.customer_name = request.form["customer_name"]
        order.place_of_supply = request.form["place_of_supply"]
        order.dispatch_date = datetime.strptime(request.form["dispatch_date"], "%Y-%m-%d")
        order.delivery_time = request.form["delivery_time"]

        # DELETE OLD PRODUCTS
        OrderItem.query.filter_by(order_id=order_id).delete()

        product_names = request.form.getlist("product_name[]")
        product_codes = request.form.getlist("product_code[]")
        quantities = request.form.getlist("quantity[]")

        for i in range(len(product_names)):
            db.session.add(OrderItem(
                order_id=order.id,
                product_name=product_names[i],
                product_code=product_codes[i],
                quantity=quantities[i]
            ))

        db.session.commit()
        return redirect(url_for("sales_dashboard"))

    return render_template("edit_order.html", order=order, items=items)

# ---------------- PRODUCTION DASHBOARD ----------------
@app.route("/production")
@login_required
def production_dashboard():
    delete_old_completed_orders()

    search = request.args.get("search")
    filter_type = request.args.get("filter")

    query = Order.query

    # -------- SEARCH FILTER --------
    if search:
        query = query.filter(
            Order.customer_name.contains(search) |
            Order.order_number.contains(search)
        )

    # -------- STATUS + KPI FILTER --------
    if filter_type == "completed":
        query = query.filter(Order.status == "Completed")

    elif filter_type == "pending":
        query = query.filter(Order.status != "Completed")

    elif filter_type == "urgent":
        today = datetime.today().date()
        query = query.filter((Order.dispatch_date - today) <= 3)

    # -------- FETCH ORDERS --------
    orders = query.order_by(Order.order_date.asc()).all()

    order_data = []

    for order in orders:

        # -------- URGENCY COLOR LOGIC --------
        today = datetime.today().date()
        diff = (order.dispatch_date - today).days

        if diff <= 3:
            color = "red"
        elif 4 <= diff <= 6:
            color = "yellow"
        else:
            color = "green"

        order_data.append({
            "order": order,
            "color": color,
            "products": OrderItem.query.filter_by(order_id=order.id).all()
        })

    # -------- DASHBOARD COUNTS --------
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(status="Completed").count()
    pending_orders = Order.query.filter(Order.status != "Completed").count()

    urgent_orders = sum(
        1 for o in Order.query.all()
        if (o.dispatch_date - datetime.today().date()).days <= 3
    )

    return render_template(
        "production_dashboard.html",
        orders=order_data,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        urgent_orders=urgent_orders
    )
# ---------------- COMPLETE ORDER ----------------
@app.route("/complete_order/<int:order_id>")
@login_required
def complete_order(order_id):

    order = Order.query.get_or_404(order_id)

    # ✅ Only production can complete order
    if current_user.role != "production":
        return redirect(url_for("production_dashboard"))

    # ✅ Prevent double completion
    if order.status == "Completed":
        return redirect(url_for("production_dashboard"))

    order.status = "Completed"
    order.completed_by = current_user.username
    order.completed_time = datetime.now()

    db.session.commit()

    return redirect(url_for("production_dashboard"))

# ---------------- REVOKE COMPLETED ORDER ----------------
@app.route("/revoke_order/<int:order_id>")
@login_required
def revoke_order(order_id):

    order = Order.query.get_or_404(order_id)

    # Only production allowed
    if current_user.role != "production":
        return redirect(url_for("production_dashboard"))

    order.status = "Pending"
    order.completed_by = None
    order.completed_time = None

    db.session.commit()

    return redirect(url_for("production_dashboard"))


# ---------------- EXPORT EXCEL REPORT ----------------
@app.route("/export_orders")
@login_required
def export_orders():

    if current_user.role != "production":
        return redirect(url_for("login"))

    orders = Order.query.all()

    data = []
    for order in orders:
        data.append({
            "Order Number": order.order_number,
            "Customer": order.customer_name,
            "Dispatch Date": order.dispatch_date,
            "Sales Person": order.sales_person,
            "Status": order.status,
            "Completed By": order.completed_by,
            "Completed Time": order.completed_time
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    return send_file(
        output,
        download_name="orders_report.xlsx",
        as_attachment=True
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- DEFAULT USERS ----------------
def create_default_users():

    password = "1234"
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")

    # ---------- ADMIN ----------
    admin_username = "Ammar.r"
    admin_password = bcrypt.generate_password_hash("AMMAR1234").decode("utf-8")

    if not User.query.filter_by(username=admin_username).first():
        db.session.add(User(
            username=admin_username,
            password=admin_password,
            role="admin"
        ))

    # ---------- PRODUCTION ----------
    for i in range(1, 4):
        username = f"production{i}"
        if not User.query.filter_by(username=username).first():
            db.session.add(User(username=username, password=hashed, role="production"))

    # ---------- SALES ----------
    for i in range(1, 11):
        username = f"sales{i}"
        if not User.query.filter_by(username=username).first():
            db.session.add(User(username=username, password=hashed, role="sales"))

    db.session.commit()

   # ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_dashboard():

    if current_user.role != "admin":
        return redirect(url_for("login"))

    # -------- CREATE USER --------
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        existing = User.query.filter_by(username=username).first()

        if not existing:

            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

            new_user = User(
                username=username,
                password=hashed_password,
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

    users = User.query.all()

    return render_template("admin_dashboard.html", users=users)

# ---------------- EDIT USER ----------------
@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):

    if current_user.role != "admin":
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    if request.method == "POST":

        new_username = request.form["username"]
        new_role = request.form["role"]
        new_password = request.form["password"]

        # ----- CHECK DUPLICATE USERNAME -----
        existing_user = User.query.filter_by(username=new_username).first()

        if existing_user and existing_user.id != user.id:
            return "Username already exists ❌"

        # ----- UPDATE USER -----
        user.username = new_username
        user.role = new_role

        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_user.html", user=user)

# ---------------- DELETE USER ----------------
@app.route("/delete_user/<int:user_id>")
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    # Prevent deleting self
    if user.username == current_user.username:
        return redirect(url_for("admin_dashboard"))

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin_dashboard"))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_default_users()

    app.run(debug=True)

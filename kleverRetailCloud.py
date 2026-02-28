import os
from flask import Flask, request, jsonify, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "kleverRetailCloud.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "kleverRetail-cloud-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ============================================================
# MODELS
# ============================================================

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)

    items = db.relationship("Item", backref="store", lazy=True)
    orders = db.relationship("Order", backref="store", lazy=True)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), default="staff")
    active = db.Column(db.Boolean, default=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    staff_username = db.Column(db.String(64))
    discount = db.Column(db.Float, default=0.0)

    lines = db.relationship("OrderLine", backref="order", lazy=True)

class OrderLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    item_name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)

# ============================================================
# HTML TEMPLATES (embedded)
# ============================================================

BASE_HTML = """
<!doctype html>
<html>
<head>
<title>kleverRetail Cloud</title>
<style>
body { font-family: Arial; background:#111827; color:#e5e7eb; margin:0; }
header { background:#0f172a; padding:10px 20px; display:flex; justify-content:space-between; }
nav a { color:#9ca3af; margin-left:15px; text-decoration:none; }
nav a:hover { color:white; }
main { padding:20px; }
table { width:100%; border-collapse:collapse; margin-top:15px; }
th,td { border:1px solid #374151; padding:6px; }
th { background:#1f2937; }
tr:nth-child(even) { background:#1f2937; }
input,select,button { padding:6px; background:#1f2937; color:#e5e7eb; border:1px solid #4b5563; }
button { background:#2563eb; border-color:#2563eb; cursor:pointer; }
button:hover { background:#1d4ed8; }
.form-row { display:flex; gap:8px; margin:10px 0; }
</style>
</head>
<body>
<header>
  <h1>kleverRetail Cloud</h1>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/stores">Stores</a>
    <a href="/items">Items</a>
    <a href="/orders">Orders</a>
    <a href="/staff">Staff</a>
  </nav>
</header>
<main>
{{ content }}
</main>
</body>
</html>
"""

def render(content):
    return render_template_string(BASE_HTML, content=content)

# ============================================================
# INITIALISE DB
# ============================================================

@app.before_first_request
def init_db():
    db.create_all()
    if Store.query.count() == 0:
        h = Store(code="HRG-001", name="Harrogate Superstore", city="Harrogate")
        db.session.add(h)
        db.session.add(Staff(username="admin", name="Admin", role="manager"))
        db.session.commit()

# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def index():
    stores = Store.query.all()
    return render(f"""
<h2>Dashboard</h2>
<p>Stores: {Store.query.count()}</p>
<p>Items: {Item.query.count()}</p>
<p>Orders: {Order.query.count()}</p>
<p>Staff: {Staff.query.count()}</p>

<h3>Stores</h3>
<ul>
{''.join(f"<li>{s.code} — {s.name} ({s.city})</li>" for s in stores)}
</ul>
""")

# ============================================================
# STORES
# ============================================================

@app.route("/stores")
def stores():
    stores = Store.query.all()
    rows = "".join(
        f"<tr><td>{s.code}</td><td>{s.name}</td><td>{s.city}</td><td>{'Yes' if s.active else 'No'}</td></tr>"
        for s in stores
    )
    return render(f"""
<h2>Stores</h2>

<form method="post" action="/stores/add" class="form-row">
  <input name="code" placeholder="Code" required>
  <input name="name" placeholder="Name" required>
  <input name="city" placeholder="City">
  <button>Add Store</button>
</form>

<table>
<tr><th>Code</th><th>Name</th><th>City</th><th>Active</th></tr>
{rows}
</table>
""")

@app.route("/stores/add", methods=["POST"])
def add_store():
    s = Store(
        code=request.form["code"],
        name=request.form["name"],
        city=request.form.get("city")
    )
    db.session.add(s)
    db.session.commit()
    return redirect("/stores")

# ============================================================
# ITEMS
# ============================================================

@app.route("/items")
def items():
    store_id = request.args.get("store_id", type=int)
    stores = Store.query.all()

    if store_id:
        items = Item.query.filter_by(store_id=store_id).all()
    else:
        items = Item.query.all()

    store_options = "".join(
        f"<option value='{s.id}' {'selected' if s.id==store_id else ''}>{s.code} — {s.name}</option>"
        for s in stores
    )

    rows = "".join(
        f"<tr><td>{i.store.code}</td><td>{i.code}</td><td>{i.name}</td><td>£{i.price:.2f}</td><td>{i.stock}</td></tr>"
        for i in items
    )

    return render(f"""
<h2>Items</h2>

<form method="get" class="form-row">
  <label>Store:</label>
  <select name="store_id" onchange="this.form.submit()">
    <option value="">All</option>
    {store_options}
  </select>
</form>

<form method="post" action="/items/add" class="form-row">
  <select name="store_id">{store_options}</select>
  <input name="code" placeholder="Code" required>
  <input name="name" placeholder="Name" required>
  <input name="price" placeholder="Price" required>
  <input name="stock" placeholder="Stock" required>
  <button>Add Item</button>
</form>

<table>
<tr><th>Store</th><th>Code</th><th>Name</th><th>Price</th><th>Stock</th></tr>
{rows}
</table>
""")

@app.route("/items/add", methods=["POST"])
def add_item():
    it = Item(
        store_id=request.form["store_id"],
        code=request.form["code"],
        name=request.form["name"],
        price=float(request.form["price"]),
        stock=int(request.form["stock"])
    )
    db.session.add(it)
    db.session.commit()
    return redirect("/items")

# ============================================================
# ORDERS
# ============================================================

@app.route("/orders")
def orders():
    store_id = request.args.get("store_id", type=int)
    stores = Store.query.all()

    if store_id:
        orders = Order.query.filter_by(store_id=store_id).order_by(Order.id.desc()).all()
    else:
        orders = Order.query.order_by(Order.id.desc()).all()

    store_options = "".join(
        f"<option value='{s.id}' {'selected' if s.id==store_id else ''}>{s.code} — {s.name}</option>"
        for s in stores
    )

    rows = "".join(
        f"<tr><td><a href='/orders/{o.id}'>{o.id}</a></td><td>{o.store.code}</td><td>{o.timestamp}</td><td>£{o.total:.2f}</td><td>{o.staff_username}</td><td>£{o.discount:.2f}</td></tr>"
        for o in orders
    )

    return render(f"""
<h2>Orders</h2>

<form method="get" class="form-row">
  <label>Store:</label>
  <select name="store_id" onchange="this.form.submit()">
    <option value="">All</option>
    {store_options}
  </select>
</form>

<table>
<tr><th>ID</th><th>Store</th><th>Time</th><th>Total</th><th>Staff</th><th>Discount</th></tr>
{rows}
</table>
""")

@app.route("/orders/<int:oid>")
def order_detail(oid):
    o = Order.query.get_or_404(oid)
    rows = "".join(
        f"<tr><td>{l.item_name}</td><td>£{l.price:.2f}</td><td>{l.qty}</td></tr>"
        for l in o.lines
    )
    return render(f"""
<h2>Order #{o.id}</h2>
<p>Store: {o.store.code} — {o.store.name}</p>
<p>Time: {o.timestamp}</p>
<p>Staff: {o.staff_username}</p>
<p>Total: £{o.total:.2f} (Discount £{o.discount:.2f})</p>

<table>
<tr><th>Item</th><th>Price</th><th>Qty</th></tr>
{rows}
</table>
""")

# ============================================================
# STAFF
# ============================================================

@app.route("/staff")
def staff():
    staff = Staff.query.all()
    rows = "".join(
        f"<tr><td>{s.username}</td><td>{s.name}</td><td>{s.role}</td><td>{'Yes' if s.active else 'No'}</td></tr>"
        for s in staff
    )
    return render(f"""
<h2>Staff</h2>

<form method="post" action="/staff/add" class="form-row">
  <input name="username" placeholder="Username" required>
  <input name="name" placeholder="Name" required>
  <input name="role" placeholder="Role">
  <button>Add Staff</button>
</form>

<table>
<tr><th>Username</th><th>Name</th><th>Role</th><th>Active</th></tr>
{rows}
</table>
""")

@app.route("/staff/add", methods=["POST"])
def add_staff():
    s = Staff(
        username=request.form["username"],
        name=request.form["name"],
        role=request.form.get("role", "staff")
    )
    db.session.add(s)
    db.session.commit()
    return redirect("/staff")

# ============================================================
# JSON API (for desktop POS sync)
# ============================================================

@app.route("/api/stores")
def api_stores():
    stores = Store.query.all()
    return jsonify([
        {"code": s.code, "name": s.name, "city": s.city, "active": s.active}
        for s in stores
    ])

@app.route("/api/items/<store_code>")
def api_items(store_code):
    store = Store.query.filter_by(code=store_code).first_or_404()
    items = Item.query.filter_by(store_id=store.id).all()
    return jsonify([
        {"code": i.code, "name": i.name, "price": i.price, "stock": i.stock}
        for i in items
    ])

@app.route("/api/orders", methods=["POST"])
def api_create_order():
    data = request.get_json(force=True)
    store_code = data.get("store_code")
    items = data.get("items", [])
    total = float(data.get("total", 0))
    discount = float(data.get("discount", 0))
    staff_username = data.get("staff_username")

    store = Store.query.filter_by(code=store_code).first()
    if not store:
        return jsonify({"error": "Unknown store"}), 400

    order = Order(
        store_id=store.id,
        total=total,
        discount=discount,
        staff_username=staff_username
    )
    db.session.add(order)
    db.session.flush()

    for it in items:
        line = OrderLine(
            order_id=order.id,
            item_name=it["name"],
            price=float(it["price"]),
            qty=int(it["qty"])
        )
        db.session.add(line)

    db.session.commit()
    return jsonify({"status": "ok", "order_id": order.id})

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)

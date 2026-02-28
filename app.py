from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import Config
from models import db, Store, Staff, Item, Order, OrderLine

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.before_first_request
    def init_db():
        db.create_all()
        if Store.query.count() == 0:
            hrg = Store(code="HRG-001", name="Harrogate Superstore", city="Harrogate")
            db.session.add(hrg)
            db.session.add(Staff(username="admin", name="Admin", role="manager"))
            db.session.commit()

    # ---------- Web pages ----------

    @app.route("/")
    def index():
        stores = Store.query.all()
        orders_count = Order.query.count()
        items_count = Item.query.count()
        staff_count = Staff.query.count()
        return render_template(
            "index.html",
            stores=stores,
            orders_count=orders_count,
            items_count=items_count,
            staff_count=staff_count,
        )

    @app.route("/stores")
    def stores():
        stores = Store.query.all()
        return render_template("stores.html", stores=stores)

    @app.route("/stores/add", methods=["POST"])
    def add_store():
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        if code and name:
            s = Store(code=code, name=name, city=city)
            db.session.add(s)
            db.session.commit()
        return redirect(url_for("stores"))

    @app.route("/items")
    def items():
        store_id = request.args.get("store_id", type=int)
        stores = Store.query.all()
        if store_id:
            items = Item.query.filter_by(store_id=store_id).all()
        else:
            items = Item.query.all()
        return render_template("items.html", stores=stores, items=items, store_id=store_id)

    @app.route("/items/add", methods=["POST"])
    def add_item():
        store_id = request.form.get("store_id", type=int)
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0) or 0)
        stock = int(request.form.get("stock", 0) or 0)
        if store_id and code and name:
            it = Item(store_id=store_id, code=code, name=name, price=price, stock=stock)
            db.session.add(it)
            db.session.commit()
        return redirect(url_for("items", store_id=store_id))

    @app.route("/orders")
    def orders():
        store_id = request.args.get("store_id", type=int)
        stores = Store.query.all()
        if store_id:
            orders = Order.query.filter_by(store_id=store_id).order_by(Order.id.desc()).all()
        else:
            orders = Order.query.order_by(Order.id.desc()).all()
        return render_template("orders.html", stores=stores, orders=orders, store_id=store_id)

    @app.route("/orders/<int:order_id>")
    def order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template("order_detail.html", order=order)

    @app.route("/staff")
    def staff():
        staff = Staff.query.all()
        return render_template("staff.html", staff=staff)

    @app.route("/staff/add", methods=["POST"])
    def add_staff():
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "staff").strip()
        if username and name:
            s = Staff(username=username, name=name, role=role)
            db.session.add(s)
            db.session.commit()
        return redirect(url_for("staff"))

    # ---------- JSON API (for kbase.py later) ----------

    @app.route("/api/stores", methods=["GET"])
    def api_stores():
        stores = Store.query.all()
        return jsonify([
            {"id": s.id, "code": s.code, "name": s.name, "city": s.city, "active": s.active}
            for s in stores
        ])

    @app.route("/api/items/<store_code>", methods=["GET"])
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
            staff_username=staff_username,
        )
        db.session.add(order)
        db.session.flush()

        for line in items:
            ol = OrderLine(
                order_id=order.id,
                item_name=line["name"],
                price=float(line["price"]),
                qty=int(line["qty"]),
            )
            db.session.add(ol)

        db.session.commit()
        return jsonify({"status": "ok", "order_id": order.id})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

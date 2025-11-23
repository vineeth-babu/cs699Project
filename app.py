from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os
import datetime

ADMIN_PASSKEY = "iitbayadmin123"


app = Flask(__name__)
app.secret_key = "iitbay_secret_key"

DATABASE = "iitbay.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buy_sell_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image TEXT,
                seller_name TEXT,
                roll_number TEXT,
                contact TEXT,
                email TEXT,
                pickup_place TEXT,
                created_at TEXT,
                status TEXT NOT NULL DEFAULT 'available',
                user_id INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lost_found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                description TEXT,
                image TEXT,
                contact TEXT,
                status TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        db.commit()


@app.route('/')
def home():
    db = get_db()
    available = db.execute("SELECT * FROM buy_sell_items WHERE status='available' ORDER BY id DESC").fetchall()
    sold = db.execute("SELECT * FROM buy_sell_items WHERE status='sold' ORDER BY id DESC").fetchall()
    return render_template('home.html', available=available, sold=sold, username=session.get('username'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')
        role_key = request.form.get('role_key')

        # Student validation
        if role == "student":
            if role_key.strip().lower() != "student":
                return render_template("register.html",
                                       error="To register as Student, type 'Student' exactly.")

        # Admin validation
        if role == "admin":
            if role_key != ADMIN_PASSKEY:
                return render_template("register.html",
                                       error="Invalid admin passkey!")

        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, password, role))
            db.commit()
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            return render_template("register.html",
                                   error="Username already exists.")

    return render_template('register.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                          (username, password)).fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
        else:
            return "Invalid credentials."
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/buy-sell')
def buy_sell():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    available = db.execute("SELECT * FROM buy_sell_items WHERE status='available' ORDER BY id DESC").fetchall()
    sold = db.execute("SELECT * FROM buy_sell_items WHERE status='sold' ORDER BY id DESC").fetchall()

    return render_template('buy_sell.html', available=available, sold=sold)


@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = request.form['price']
        seller_name = request.form['seller_name']
        roll_number = request.form.get('roll_number')
        contact = request.form.get('contact')
        email = request.form.get('email')
        pickup_place = request.form.get('pickup_place')

        image_file = request.files.get("image")
        filename = None
        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db = get_db()
        db.execute("""
            INSERT INTO buy_sell_items
            (name, description, price, image, seller_name, roll_number, contact, email, pickup_place, created_at, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?)
        """, (name, description, price, filename, seller_name, roll_number, contact,
              email, pickup_place, created_at, session['user_id']))

        db.commit()
        return redirect(url_for('buy_sell'))

    return render_template('add_item.html')


@app.route('/your-products')
def your_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()

    buy_sell_items = db.execute(
        "SELECT * FROM buy_sell_items WHERE user_id = ? ORDER BY id DESC",
        (session['user_id'],)
    ).fetchall()

    lost_found_items = db.execute(
        "SELECT * FROM lost_found_items WHERE user_id = ? ORDER BY id DESC",
        (session['user_id'],)
    ).fetchall()

    return render_template(
        'your_products.html',
        buy_sell_items=buy_sell_items,
        lost_found_items=lost_found_items
    )


@app.route('/product/<int:item_id>')
def product_detail(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        return "Item not found.", 404

    return render_template('product_detail.html', item=item)


@app.route('/product/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_product(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        existing_image = request.form.get("existing_image")

        image_file = request.files.get("image")
        filename = existing_image

        if image_file and image_file.filename != "":
            if allowed_file(image_file.filename):
                filename = image_file.filename
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute("""
            UPDATE buy_sell_items
            SET name=?, description=?, price=?, image=?
            WHERE id=?
        """, (name, description, price, filename, item_id))

        db.commit()
        return redirect(url_for('product_detail', item_id=item_id))

    return render_template('edit_product.html', item=item)


@app.route('/product/<int:item_id>/delete')
def delete_product(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    db.execute("DELETE FROM buy_sell_items WHERE id=?", (item_id,))
    db.commit()

    return redirect(url_for('buy_sell'))


@app.route('/product/<int:item_id>/sold')
def mark_sold(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    db.execute("UPDATE buy_sell_items SET status='sold' WHERE id=?", (item_id,))
    db.commit()

    return redirect(url_for('product_detail', item_id=item_id))


@app.route('/lost-found')
def lost_found():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()

    active_items = db.execute("""
        SELECT * FROM lost_found_items 
        WHERE status != 'resolved'
        ORDER BY id DESC
    """).fetchall()

    resolved_items = db.execute("""
        SELECT * FROM lost_found_items 
        WHERE status = 'resolved'
        ORDER BY id DESC
    """).fetchall()

    return render_template(
        'lost_found.html',
        active_items=active_items,
        resolved_items=resolved_items
    )


@app.route('/add-lost-item', methods=['GET', 'POST'])
def add_lost_item():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        item = request.form['item']
        description = request.form.get('description')
        contact = request.form.get('contact')
        status = request.form['status']

        image_file = request.files.get("image")
        filename = None

        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db = get_db()
        db.execute(
            "INSERT INTO lost_found_items (item, description, image, contact, status, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (item, description, filename, contact, status, session['user_id'])
        )
        db.commit()

        return redirect(url_for('lost_found'))

    return render_template('add_lost_item.html')


@app.route('/lost-found/<int:item_id>')
def lost_found_detail(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM lost_found_items WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        return "Item not found.", 404

    return render_template('lostfound_detail.html', item=item)


@app.route('/lost-found/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_lost_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM lost_found_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    if request.method == 'POST':
        name = request.form['item']
        description = request.form['description']
        contact = request.form['contact']
        status = request.form['status']

        existing_image = request.form.get("existing_image")
        image_file = request.files.get("image")
        filename = existing_image

        if image_file and image_file.filename != "":
            if allowed_file(image_file.filename):
                filename = image_file.filename
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute("""
            UPDATE lost_found_items
            SET item=?, description=?, contact=?, status=?, image=?
            WHERE id=?
        """, (name, description, contact, status, filename, item_id))

        db.commit()
        return redirect(url_for('lost_found_detail', item_id=item_id))

    return render_template('edit_lost_item.html', item=item)


@app.route('/lost-found/<int:item_id>/delete')
def delete_lost_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM lost_found_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    db.execute("DELETE FROM lost_found_items WHERE id=?", (item_id,))
    db.commit()

    return redirect(url_for('lost_found'))


@app.route('/lost-found/<int:item_id>/resolve')
def resolve_lost_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM lost_found_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."
    if item['user_id'] != session['user_id']:
        return "Not allowed."

    db.execute("UPDATE lost_found_items SET status='resolved' WHERE id=?", (item_id,))
    db.commit()

    return redirect(url_for('lost_found_detail', item_id=item_id))


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, port=5001)

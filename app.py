from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import datetime
import razorpay
import smtplib
import ssl
import requests
from bs4 import BeautifulSoup
import json
import re

ADMIN_PASSKEY = "iitbayadmin123"

app = Flask(__name__)
app.secret_key = "iitbay_secret_key"

DATABASE = "iitbay.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

RAZORPAY_KEY_ID = "rzp_test_Rjxas830z4dGHQ"
RAZORPAY_KEY_SECRET = "4toRYXDU0LiIQGnDFN1MfqaG"

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def ensure_column(cursor, table_name, column_name, column_def):
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [row["name"] for row in cursor.fetchall()]
    if column_name not in cols:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """
        )
        ensure_column(cursor, "users", "email", "TEXT")

        cursor.execute(
            """
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
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lost_found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                description TEXT,
                image TEXT,
                contact TEXT,
                status TEXT NOT NULL,
                user_id INTEGER
            )
        """
        )
        ensure_column(cursor, "lost_found_items", "category", "TEXT")
        ensure_column(cursor, "lost_found_items", "created_at", "TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_type TEXT NOT NULL,
                chat_item_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                link TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """
        )
        ensure_column(cursor, "notifications", "type", "TEXT")
        ensure_column(cursor, "notifications", "chat_type", "TEXT")
        ensure_column(cursor, "notifications", "chat_item_id", "INTEGER")

        db.commit()


def send_email_notification(to_email, subject, body):
    if not to_email:
        return

    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = os.environ.get("IITBAY_EMAIL")         
    password = os.environ.get("IITBAY_EMAIL_PASSWORD") 

    if not sender_email or not password:
        print("EMAIL (dev mode) TO:", to_email)
        print("SUBJECT:", subject)
        print("BODY:", body)
        return

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, to_email, message)
        print("Email sent successfully")
    except Exception as e:
        print("Email send failed:", e)

# def get_market_price(product_name):
#     import requests
#     from bs4 import BeautifulSoup
#     import re

#     try:
#         print(f"\n🔍 Searching pricehistory.app for: {product_name}")

#         query = product_name.replace(" ", "%20")
#         url = f"https://pricehistory.app/page/search#gsc.tab=0&gsc.q={query}"

#         headers = {
#             "User-Agent": (
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36 (KHTML, like Gecko) "
#                 "Chrome/120.0.0.0 Safari/537.36"
#             )
#         }

#         res = requests.get(url, headers=headers, timeout=8)
#         print("Status:", res.status_code)

#         if res.status_code != 200:
#             print("❌ Request failed")
#             return None

#         soup = BeautifulSoup(res.text, "html.parser")

#         # Select Google CSE snippet blocks
#         snippets = soup.select(".gs-snippet, .gs-bidi-start-align")

#         if not snippets:
#             print("❌ No snippet blocks found")
#             return None

#         # Join text for regex search
#         combined = " ".join(s.get_text(" ", strip=True) for s in snippets)

#         print("\n🔎 Combined Snippet Text:\n", combined[:300], "...\n")

#         # Extract ₹ values
#         prices = re.findall(r"₹\s?[\d,]+", combined)

#         if not prices:
#             print("❌ No price found")
#             return None

#         # FIRST price is "current price"
#         price = prices[0].replace("₹", "").replace(",", "").strip()

#         if price.isdigit():
#             final_price = int(price)
#             print("✔ Extracted Current Price:", final_price)
#             return final_price

#         print("❌ Extracted price invalid:", price)
#         return None

#     except Exception as e:
#         print("❌ Exception:", e)
#         return None







@app.context_processor
def inject_notification_info():
    """Inject unread notification count + preview into all templates."""
    notif_unread_count = 0
    notif_preview = []

    if "user_id" in session:
        try:
            db = get_db()
            user_id = session["user_id"]
            row = db.execute(
                "SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND is_read=0",
                (user_id,),
            ).fetchone()
            notif_unread_count = row["c"] if row else 0

            notif_preview = db.execute(
                """
                SELECT * FROM notifications
                WHERE user_id=? AND is_read=0
                ORDER BY created_at DESC
                LIMIT 20
            """,
                (user_id,),
            ).fetchall()
        except Exception as e:
            print("Notification inject error:", e)

    return dict(
        notif_unread_count=notif_unread_count, notif_preview=notif_preview
    )

@app.route("/")
def home():
    db = get_db()
    available = db.execute(
        "SELECT * FROM buy_sell_items WHERE status='available' ORDER BY id DESC"
    ).fetchall()
    sold = db.execute(
        "SELECT * FROM buy_sell_items WHERE status='sold' ORDER BY id DESC"
    ).fetchall()
    return render_template(
        "home.html", available=available, sold=sold, username=session.get("username")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form.get("email")
        role = request.form.get("role")
        role_key = request.form.get("role_key")

        if role == "student":
            if role_key.strip().lower() != "student":
                return render_template(
                    "register.html",
                    error="To register as Student, type 'Student' exactly.",
                )

        if role == "admin":
            if role_key != ADMIN_PASSKEY:
                return render_template(
                    "register.html", error="Invalid admin passkey!"
                )

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                (username, password, role, email),
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password),
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("home"))
        else:
            return "Invalid credentials."

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/buy-sell")
def buy_sell():
    if "username" not in session:
        return redirect(url_for("login"))

    db = get_db()
    available = db.execute(
        "SELECT * FROM buy_sell_items WHERE status='available' ORDER BY id DESC"
    ).fetchall()
    sold = db.execute(
        "SELECT * FROM buy_sell_items WHERE status='sold' ORDER BY id DESC"
    ).fetchall()

    return render_template("buy_sell.html", available=available, sold=sold)


@app.route("/add-item", methods=["GET", "POST"])
def add_item():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        price = request.form["price"]
        seller_name = request.form["seller_name"]
        roll_number = request.form.get("roll_number")
        contact = request.form.get("contact")
        email = request.form.get("email")
        pickup_place = request.form.get("pickup_place")

        image_file = request.files.get("image")
        filename = None
        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db = get_db()
        db.execute(
            """
            INSERT INTO buy_sell_items
            (name, description, price, image, seller_name, roll_number, contact, email, pickup_place,
             created_at, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?)
        """,
            (
                name,
                description,
                price,
                filename,
                seller_name,
                roll_number,
                contact,
                email,
                pickup_place,
                created_at,
                session["user_id"],
            ),
        )
        db.commit()
        return redirect(url_for("buy_sell"))

    return render_template("add_item.html")


@app.route("/your-products")
def your_products():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    buy_sell_items = db.execute(
        "SELECT * FROM buy_sell_items WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()

    lost_found_items = db.execute(
        "SELECT * FROM lost_found_items WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()

    return render_template(
        "your_products.html",
        buy_sell_items=buy_sell_items,
        lost_found_items=lost_found_items,
    )


@app.route("/product/<int:item_id>")
def product_detail(item_id):
    if "username" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        return "Item not found.", 404

    # # Get market price from Flipkart
    # market_price = get_market_price(item["name"])

    return render_template(
        "product_detail.html",
        item=item,
        # market_price=market_price
    )






@app.route("/product/<int:item_id>/edit", methods=["GET", "POST"])
def edit_product(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        existing_image = request.form.get("existing_image")

        image_file = request.files.get("image")
        filename = existing_image
        if image_file and image_file.filename != "":
            if allowed_file(image_file.filename):
                filename = image_file.filename
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute(
            """
            UPDATE buy_sell_items
            SET name=?, description=?, price=?, image=?
            WHERE id=?
        """,
            (name, description, price, filename, item_id),
        )
        db.commit()
        return redirect(url_for("product_detail", item_id=item_id))

    return render_template("edit_product.html", item=item)


@app.route("/product/<int:item_id>/delete")
def delete_product(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    db.execute("DELETE FROM buy_sell_items WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("buy_sell"))


@app.route("/product/<int:item_id>/sold")
def mark_sold(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    db.execute("UPDATE buy_sell_items SET status='sold' WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("product_detail", item_id=item_id))

@app.route("/lost-found")
def lost_found():
    if "username" not in session:
        return redirect(url_for("login"))

    db = get_db()
    active_items = db.execute(
        "SELECT * FROM lost_found_items WHERE status!='resolved' ORDER BY id DESC"
    ).fetchall()
    resolved_items = db.execute(
        "SELECT * FROM lost_found_items WHERE status='resolved' ORDER BY id DESC"
    ).fetchall()

    return render_template(
        "lost_found.html",
        active_items=active_items,
        resolved_items=resolved_items,
    )


@app.route("/add-lost-item", methods=["GET", "POST"])
def add_lost_item():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        item = request.form["item"]
        description = request.form.get("description")
        contact = request.form.get("contact")
        status = request.form["status"]
        category = request.form.get("category")
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        image_file = request.files.get("image")
        filename = None
        if image_file and allowed_file(image_file.filename):
            filename = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO lost_found_items (item, description, image, contact, status, user_id, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (item, description, filename, contact, status, session["user_id"], category, created_at),
        )
        lost_item_id = cursor.lastrowid
        if category:
            if status.lower() == "found":
                lost_rows = db.execute(
                    """
                    SELECT DISTINCT l.id AS lost_id, l.user_id, u.email
                    FROM lost_found_items l
                    JOIN users u ON u.id = l.user_id
                    WHERE l.status='lost' AND l.category=? 
                """,
                    (category,),
                ).fetchall()

                for row in lost_rows:
                    uid = row["user_id"]
                    email = row["email"]
                    lost_id = row["lost_id"]

                    msg = f"A new FOUND item was posted in '{category}'. Check if it matches your lost item."
                    link = url_for("lost_found_detail", item_id=lost_item_id)

                    db.execute(
                        """
                        INSERT INTO notifications (user_id, message, link, is_read, created_at, type)
                        VALUES (?, ?, ?, 0, ?, 'lost_found')
                    """,
                        (uid, msg, link, created_at),
                    )

                    subject = "IITBay Lost & Found: A matching FOUND item detected"
                    body = (
                        f"A newly posted FOUND item in category '{category}' might match your lost item.\n\n"
                        f"Found item posted: {item}\n"
                        f"Please check the app.\n"
                    )
                    try: 
                        send_email_notification(email,subject, body)
                    except Exception as e:
                        print("Email failed but notification is created")

            if status.lower() == "lost":
                found_rows = db.execute(
                    """
                    SELECT DISTINCT f.id AS found_id, f.user_id, u.email
                    FROM lost_found_items f
                    JOIN users u ON u.id = f.user_id
                    WHERE f.status='found' AND f.category=?
                """,
                    (category,),
                ).fetchall()

                for row in found_rows:
                    uid = row["user_id"]
                    email = row["email"]
                    found_id = row["found_id"]

                    msg = f"Someone LOST an item in '{category}'. It may match the item you posted as FOUND."
                    link = url_for("lost_found_detail", item_id=lost_item_id)

                    db.execute(
                        """
                        INSERT INTO notifications (user_id, message, link, is_read, created_at, type)
                        VALUES (?, ?, ?, 0, ?, 'lost_found')
                    """,
                        (uid, msg, link, created_at),
                    )

                    subject = "IITBay Lost & Found: A matching LOST item detected"
                    body = (
                        f"Someone posted a LOST item in category '{category}'.\n\n"
                        f"It might match the item you posted as FOUND.\n"
                        f"Lost item posted: {item}\n"
                        f"Please check in the app.\n"
                    )
                    try: 
                        send_email_notification(email,subject, body)
                    except Exception as e:
                        print("Email failed but notification is created")
                    

        db.commit()
        return redirect(url_for("lost_found"))

    return render_template("add_lost_item.html")


@app.route('/lost-found/<int:item_id>')
def lost_found_detail(item_id):
    if "username" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute(
        "SELECT * FROM lost_found_items WHERE id=?", (item_id,)
    ).fetchone()
    if item is None:
        return "Item not found.", 404

    return render_template("lostfound_detail.html", item=item)


@app.route("/lost-found/<int:item_id>/edit", methods=["GET", "POST"])
def edit_lost_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute(
        "SELECT * FROM lost_found_items WHERE id=?", (item_id,)
    ).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    if request.method == "POST":
        name = request.form["item"]
        description = request.form["description"]
        contact = request.form["contact"]
        status = request.form["status"]
        category = request.form.get("category")

        existing_image = request.form.get("existing_image")
        image_file = request.files.get("image")
        filename = existing_image
        if image_file and image_file.filename != "":
            if allowed_file(image_file.filename):
                filename = image_file.filename
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute(
            """
            UPDATE lost_found_items
            SET item=?, description=?, contact=?, status=?, image=?, category=?
            WHERE id=?
        """,
            (name, description, contact, status, filename, category, item_id),
        )
        db.commit()
        return redirect(url_for("lost_found_detail", item_id=item_id))

    return render_template("edit_lost_item.html", item=item)


@app.route("/lost-found/<int:item_id>/delete")
def delete_lost_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute(
        "SELECT * FROM lost_found_items WHERE id=?", (item_id,)
    ).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    db.execute("DELETE FROM lost_found_items WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("lost_found"))


@app.route("/lost-found/<int:item_id>/resolve")
def resolve_lost_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    item = db.execute(
        "SELECT * FROM lost_found_items WHERE id=?", (item_id,)
    ).fetchone()
    if item is None:
        return "Item not found."
    if item["user_id"] != session["user_id"]:
        return "Not allowed."

    db.execute("UPDATE lost_found_items SET status='resolved' WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("lost_found_detail", item_id=item_id))


@app.route("/chat/<chat_type>/<int:item_id>")
def chat_page(chat_type, item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    if chat_type == "buy":
        item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
        item_title = item["name"] if item else ""
        back_url = url_for("product_detail", item_id=item_id)
    else:
        item = db.execute("SELECT * FROM lost_found_items WHERE id=?", (item_id,)).fetchone()
        item_title = item["item"] if item else ""
        back_url = url_for("lost_found_detail", item_id=item_id)

    if item is None:
        return "Item not found.", 404

    user_id = session["user_id"]
    owner_id = item["user_id"]
    other_user_id = request.args.get("chat_with", type=int)

    chat_buyers = []
    current_chat_partner = None
    chat_messages = []

    if user_id == owner_id:
        chat_buyers = db.execute(
            """
            SELECT DISTINCT u.id, u.username
            FROM chat_messages cm
            JOIN users u ON u.id = cm.sender_id
            WHERE cm.chat_type=? AND cm.chat_item_id=? AND cm.sender_id != ?
        """,
            (chat_type, item_id, owner_id),
        ).fetchall()

        if other_user_id is None and chat_buyers:
            other_user_id = chat_buyers[0]["id"]

        if other_user_id:
            current_chat_partner = db.execute(
                "SELECT * FROM users WHERE id=?", (other_user_id,)
            ).fetchone()
    else:
        other_user_id = owner_id
        current_chat_partner = db.execute(
            "SELECT * FROM users WHERE id=?", (owner_id,)
        ).fetchone()

    if current_chat_partner:
        chat_messages = db.execute(
            """
            SELECT cm.*, u.username AS sender_name
            FROM chat_messages cm
            JOIN users u ON u.id = cm.sender_id
            WHERE cm.chat_type=? AND cm.chat_item_id=?
              AND (
                    (cm.sender_id=? AND cm.receiver_id=?)
                 OR (cm.sender_id=? AND cm.receiver_id=?)
              )
            ORDER BY cm.created_at ASC
        """,
            (chat_type, item_id, user_id, other_user_id, other_user_id, user_id),
        ).fetchall()

    db.execute(
        """
        UPDATE notifications
        SET is_read=1
        WHERE user_id=?
          AND type='chat'
          AND (
                (chat_type=? AND chat_item_id=?)
             OR link LIKE ?
              )
        """,
        (user_id, chat_type, item_id, f"%/chat/{chat_type}/{item_id}%"),
    )
    db.commit()

    return render_template(
        "product_detail.html" if chat_type == "buy" else "lostfound_detail.html",
        chat_type=chat_type,
        chat_item=item,
        item=item,
        item_title=item_title,
        chat_open=True,
        chat_messages=chat_messages,
        chat_buyers=chat_buyers,
        current_chat_partner=current_chat_partner,
        back_url=back_url,
    )

@app.route("/chat/<chat_type>/<int:item_id>/send", methods=["POST"])
def send_chat_message(chat_type, item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    if chat_type == "buy":
        item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()
        item_title = item["name"] if item else ""
    else:
        item = db.execute("SELECT * FROM lost_found_items WHERE id=?", (item_id,)).fetchone()
        item_title = item["item"] if item else ""

    if item is None:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": "Item not found"}), 404
        return "Item not found.", 404

    user_id = session["user_id"]
    owner_id = item["user_id"]
    other_user_id = request.form.get("other_user_id", type=int)
    message = request.form.get("message", "").strip()

    if not message:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": "Empty message"}), 400
        return redirect(url_for("chat_page", chat_type=chat_type, item_id=item_id))

    if user_id == owner_id:
        if not other_user_id:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": "No partner selected"}), 400
            return "No partner selected.", 400
        receiver_id = other_user_id
    else:
        receiver_id = owner_id
        other_user_id = owner_id

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute(
        """
        INSERT INTO chat_messages (chat_type, chat_item_id, sender_id, receiver_id, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (chat_type, item_id, user_id, receiver_id, message, created_at),
    )
    db.commit()

    sender_row = db.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    sender_name = sender_row["username"] if sender_row else "Someone"

    base_msg = f"New messages about '{item_title}'."
    link = url_for("chat_page", chat_type=chat_type, item_id=item_id)

    existing = db.execute(
        """
        SELECT * FROM notifications
        WHERE user_id=? AND type='chat' AND chat_type=? AND chat_item_id=? AND is_read=0
    """,
        (receiver_id, chat_type, item_id),
    ).fetchone()

    if existing:
        db.execute(
            """
            UPDATE notifications
            SET message=?, link=?, created_at=?, chat_type=?, chat_item_id=?
            WHERE id=?
        """,
            (base_msg, link, created_at, chat_type, item_id, existing["id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO notifications (user_id, message, link, is_read, created_at, type, chat_type, chat_item_id)
            VALUES (?, ?, ?, 0, ?, 'chat', ?, ?)
        """,
            (receiver_id, base_msg, link, created_at, chat_type, item_id),
        )

    db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "message_id": db.execute("SELECT last_insert_rowid() AS id").fetchone()[0]})

    return redirect(url_for("chat_page", chat_type=chat_type, item_id=item_id, chat_with=other_user_id))



@app.route("/chat/messages/<chat_type>/<int:item_id>")
def get_chat_messages(chat_type, item_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    user_id = session["user_id"]
    partner_id = request.args.get("partner", type=int)
    if not partner_id:
        return jsonify({"messages": []})

    rows = db.execute(
        """
        SELECT cm.*, u.username AS sender_name
        FROM chat_messages cm
        JOIN users u ON u.id = cm.sender_id
        WHERE cm.chat_type=? AND cm.chat_item_id=?
          AND (
                (cm.sender_id=? AND cm.receiver_id=?)
             OR (cm.sender_id=? AND cm.receiver_id=?)
          )
        ORDER BY cm.created_at ASC
    """,
        (chat_type, item_id, user_id, partner_id, partner_id, user_id),
    ).fetchall()

    messages = []
    for r in rows:
        messages.append(
            {
                "id": r["id"],
                "sender_id": r["sender_id"],
                "sender_name": r["sender_name"],
                "message": r["message"],
                "created_at": r["created_at"],
                "is_me": r["sender_id"] == user_id,
            }
        )

    return jsonify({"messages": messages})

@app.route("/notifications/mark_read", methods=["POST"])
def mark_notifications_read():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    notif_id = data.get("id")

    db = get_db()
    if notif_id:
        db.execute(
            "UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?",
            (notif_id, session["user_id"])
        )
    else:
        db.execute(
            "UPDATE notifications SET is_read=1 WHERE user_id=?",
            (session["user_id"],)
        )

    db.commit()
    return jsonify({"ok": True})


@app.route("/notifications/fetch")
def fetch_notifications():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    db = get_db()
    user_id = session["user_id"]

    rows = db.execute("""
        SELECT id, message, link, created_at, type
        FROM notifications
        WHERE user_id=? AND is_read=0
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,)).fetchall()

    notifs = []
    for r in rows:
        notifs.append({
            "id": r["id"],
            "message": r["message"],
            "link": r["link"],
            "created_at": r["created_at"],
            "type": r["type"]
        })

    count = len(notifs)

    return jsonify({"success": True, "count": count, "notifications": notifs})




@app.route('/create-order/<int:item_id>', methods=['POST'])
def create_order(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id=?", (item_id,)).fetchone()

    if item is None:
        return "Item not found", 404

    amount = int(float(item['price']) * 100)  # convert ₹ to paise

    razorpay_order = razorpay_client.order.create(dict(
        amount=amount,
        currency="INR",
        payment_capture="1"
    ))

    return render_template(
        "pay.html",
        item=item,
        razorpay_order_id=razorpay_order["id"],
        razorpay_key_id=RAZORPAY_KEY_ID,
        amount=amount
    )

@app.route('/payment-success', methods=['POST'])
def payment_success():
    data = request.get_json()

    item_id = data.get("item_id")

    # mark item as sold after payment
    db = get_db()
    db.execute("UPDATE buy_sell_items SET status='sold' WHERE id=?", (item_id,))
    db.commit()

    return {"message": "Payment successful! Item marked as sold."}






if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, port=5001)

import os
from functools import wraps

import mysql.connector
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST", "127.0.0.1")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DATABASE"] = os.environ.get("MYSQL_DATABASE", "flask_crud_app")
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 3306))


def get_server_connection():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        port=app.config["MYSQL_PORT"],
    )


def get_db_connection():
    if "db_connection" not in g:
        g.db_connection = mysql.connector.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
            port=app.config["MYSQL_PORT"],
        )
    return g.db_connection


@app.teardown_appcontext
def close_db_connection(_error):
    connection = g.pop("db_connection", None)
    if connection is not None and connection.is_connected():
        connection.close()


def init_database():
    try:
        server_connection = get_server_connection()
        server_cursor = server_connection.cursor()
        server_cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{app.config['MYSQL_DATABASE']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_cursor.close()
        server_connection.close()

        db_connection = mysql.connector.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
            port=app.config["MYSQL_PORT"],
        )
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(150) NOT NULL,
                description TEXT,
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_items_users
                    FOREIGN KEY (created_by) REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )
        db_connection.commit()
        db_cursor.close()
        db_connection.close()
    except Error as exc:
        raise RuntimeError(
            "Database initialization failed. "
            "Check your XAMPP MySQL service and connection settings."
        ) from exc


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None

    if user_id is None:
        return

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    g.user = cursor.fetchone()
    cursor.close()


@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")

        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, generate_password_hash(password)),
        )
        connection.commit()
        cursor.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, title, description, created_at, updated_at
        FROM items
        WHERE created_by = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],),
    )
    items = cursor.fetchall()
    cursor.close()
    return render_template("dashboard.html", items=items)


@app.route("/items/create", methods=["GET", "POST"])
@login_required
def create_item():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Title is required.", "danger")
            return render_template("item_form.html", item=None, action="Create")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO items (title, description, created_by) VALUES (%s, %s, %s)",
            (title, description, session["user_id"]),
        )
        connection.commit()
        cursor.close()

        flash("Item created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("item_form.html", item=None, action="Create")


def get_item_or_404(item_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, title, description, created_by, created_at, updated_at
        FROM items
        WHERE id = %s AND created_by = %s
        """,
        (item_id, session["user_id"]),
    )
    item = cursor.fetchone()
    cursor.close()
    return item


@app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = get_item_or_404(item_id)
    if item is None:
        flash("Item not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Title is required.", "danger")
            return render_template("item_form.html", item=item, action="Update")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE items SET title = %s, description = %s WHERE id = %s AND created_by = %s",
            (title, description, item_id, session["user_id"]),
        )
        connection.commit()
        cursor.close()

        flash("Item updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("item_form.html", item=item, action="Update")


@app.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = get_item_or_404(item_id)
    if item is None:
        flash("Item not found.", "danger")
        return redirect(url_for("dashboard"))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM items WHERE id = %s AND created_by = %s",
        (item_id, session["user_id"]),
    )
    connection.commit()
    cursor.close()

    flash("Item deleted successfully.", "success")
    return redirect(url_for("dashboard"))


@app.context_processor
def inject_app_name():
    return {"app_name": "Flask CRUD App"}


if __name__ == "__main__":
    init_database()
    app.run(debug=True)

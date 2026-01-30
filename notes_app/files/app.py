from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "very-secret-key"

# ------------------ CONFIG ------------------
DB_FILE = "/opt/notes-app/notes.db"  # Path to SQLite DB

# ------------------ INIT DATABASE ------------------
def init_db():
    if not os.path.exists(DB_FILE):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        # Create users table
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        # Create notes table
        cur.execute("""
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

# Initialize database on startup
init_db()

# ------------------ DATABASE CONNECTION ------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            return "Username and password are required."

        password_hash = generate_password_hash(password)

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            db.commit()
        except sqlite3.IntegrityError:
            cur.close()
            db.close()
            return "Username already exists."
        cur.close()
        db.close()
        return redirect("/login")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Notes - Register</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            html, body { height: 100%; margin: 0; background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }
            body { display: flex; justify-content: center; align-items: center; }
            .card { padding: 30px; border-radius: 15px; width: 100%; max-width: 400px; }
        </style>
    </head>
    <body>
        <div class="card bg-white shadow">
            <h2 class="text-center text-primary mb-4">My Notes - Register</h2>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input class="form-control" name="username" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <input class="form-control" type="password" name="password" required>
                </div>
                <button class="btn btn-success w-100">Register</button>
            </form>
            <p class="mt-3 text-center"><a href="/login">Already have an account? Login</a></p>
        </div>
    </body>
    </html>
    """
    return html

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/")
        return "Invalid credentials."

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Notes - Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            html, body { height: 100%; margin: 0; background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }
            body { display: flex; justify-content: center; align-items: center; }
            .card { padding: 30px; border-radius: 15px; width: 100%; max-width: 400px; }
        </style>
    </head>
    <body>
        <div class="card bg-white shadow">
            <h2 class="text-center text-primary mb-4">My Notes - Login</h2>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input class="form-control" name="username" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <input class="form-control" type="password" name="password" required>
                </div>
                <button class="btn btn-primary w-100">Login</button>
            </form>
            <p class="mt-3 text-center"><a href="/register">Don't have an account? Register</a></p>
        </div>
    </body>
    </html>
    """
    return html

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------ DASHBOARD / NOTES ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        note_content = request.form["note"].strip()
        if note_content:
            cur.execute(
                "INSERT INTO notes (user_id, content) VALUES (?, ?)",
                (session["user_id"], note_content)
            )
            db.commit()

    cur.execute(
        "SELECT content, created_at FROM notes WHERE user_id=? ORDER BY created_at DESC",
        (session["user_id"],)
    )
    notes = cur.fetchall()
    cur.close()
    db.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Notes Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            html, body { height: 100%; margin: 0; background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }
            body { display: flex; justify-content: center; align-items: center; }
            .container { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; width: 90%; max-width: 900px; height: 90%; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.3); display: flex; flex-direction: column; }
            h1 { text-align: center; margin-bottom: 20px; }
            .notes { overflow-y: auto; flex-grow: 1; margin-top: 15px; }
            .note-card { background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
            textarea { resize: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>My Notes</h1>
            <form method="POST" class="mb-3">
                <div class="mb-2">
                    <textarea class="form-control" name="note" rows="3" placeholder="Write your note here..." required></textarea>
                </div>
                <button class="btn btn-primary w-100">Add Note</button>
            </form>
            <div class="notes">
                {% if notes %}
                    {% for n in notes %}
                        <div class="note-card">
                            <small class="text-muted">{{ n['created_at'] }}</small>
                            <p>{{ n['content'] }}</p>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No notes yet. Start by adding one above!</p>
                {% endif %}
            </div>
            <a href="/logout" class="btn btn-danger mt-3">Logout</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, notes=notes)

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# Import Flask and helper functions to handle requests and return JSON
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import sqlite3 to interact with SQLite database
import sqlite3

# Import secure password functions (never store raw passwords)
from werkzeug.security import generate_password_hash, check_password_hash

# Create a Flask app object
app = Flask(__name__)
CORS(app)

# Function to open a connection to the SQLite database
def get_db():
    conn = sqlite3.connect("users.db")   # Opens users.db
    conn.row_factory = sqlite3.Row       # Makes rows behave like dictionaries
    return conn


# -------------------------
#      SIGNUP ROUTE
# -------------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json   # Get JSON data sent by the frontend

    # Extract fields from JSON
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # Check that all 3 fields are present
    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    # Hash the password so we never store raw passwords
    password_hash = generate_password_hash(password)

    # Connect to database
    conn = get_db()
    cur = conn.cursor()

    try:
        # Insert user details into the database
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()  # Save changes
    except sqlite3.IntegrityError:
        # This error happens when the email already exists (because it is UNIQUE)
        return jsonify({"error": "Email already exists"}), 409
    finally:
        conn.close()   # Close the DB connection

    # Send back success response
    return jsonify({"message": "User created successfully"}), 201


# -------------------------
#        LOGIN ROUTE
# -------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json   # Get JSON request body
    email = data.get("email")
    password = data.get("password")

    # Connect to database
    conn = get_db()
    cur = conn.cursor()

    # Look up user by email
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()

    # If no user is found
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Check if password matches the stored hash
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Incorrect password"}), 401

    # If login succeeded
    return jsonify({"message": "Login successful", "name": user["name"]}), 200

# -------------------------
# VIEW ALL USERS (DEBUG)
# -------------------------
@app.route("/users", methods=["GET"])
def get_all_users():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, name, email FROM users")
    rows = cur.fetchall()
    conn.close()

    users = [dict(row) for row in rows]

    return jsonify(users), 200

# Run the server
if __name__ == "__main__":
    app.run(debug=True)   # debug=True auto reloads on file changes



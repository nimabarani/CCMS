import os
from flask import Flask, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from utils.validators import validate_email, validate_password
from utils.common import hash_password
from utils.db import get_db_connection


# Load environment variables from .env file
load_dotenv()

# Initialize Flask app for the admin panel
app = Flask(__name__)


@app.route("/")
def admin_home():
    """Serves the admin panel's main HTML page."""
    try:
        return send_file("templates/admin.html")
    except FileNotFoundError:
        app.logger.error("templates/admin.html not found")
        return "Admin panel page not found.", 404


@app.route("/create-user", methods=["POST"])
def create_user():
    """
    Handles the creation of a new advisor user.
    This endpoint is intentionally open and does not require a login,
    as its purpose is to create the initial users.
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Input Validation
    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Validate password
    is_valid, error_message = validate_password(password)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    if not validate_email(email):
        return jsonify({"message": "Invalid email format"}), 400

    # User Creation Logic
    salt = os.urandom(16).hex()
    password_hash = hash_password(password, salt)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO public.user_credentials (email, password_hash, salt)
            VALUES (%s, %s, %s)
            """,
            (email, password_hash, salt),
        )
        conn.commit()
        return jsonify({"message": "Advisor user created successfully"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"message": "Email already exists"}), 409
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error creating user: {e}")
        return jsonify({"message": "An error occurred while creating the user"}), 500
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # Admin panel on port 5001 to avoid unauthorized access
    app.run(host="0.0.0.0", debug=True, port=5001)

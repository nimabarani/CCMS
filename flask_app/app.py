import os
from flask import Flask, request, jsonify, session, send_file
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from utils.validators import validate_email, validate_password
from utils.common import hash_password
from utils.db import get_db_connection


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24).hex())
app.config["SESSION_COOKIE_HTTPONLY"] = True
# app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is required")


@app.route("/")
def index():
    try:
        return send_file("templates/index.html")
    except FileNotFoundError:
        app.logger.error("templates/index.html not found")
        return jsonify({"message": "Page not found"}), 404


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not validate_email(email):
        return jsonify({"message": "Invalid email format"}), 400

    is_valid, error_message = validate_password(password)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get advisor credentials
    cur.execute(
        """
        SELECT
          user_id,
          email,
          password_hash,
          salt
        FROM
          public.user_credentials
        WHERE email = %s
        """,
        (email,),
    )

    advisor = cur.fetchone()
    cur.close()
    conn.close()

    if advisor and advisor["password_hash"] == hash_password(password, advisor["salt"]):
        session["advisor_id"] = advisor["user_id"]
        session["advisor_email"] = advisor["email"]
        return jsonify({"message": "Login successful", "email": advisor["email"]}), 200
    return jsonify({"message": "Invalid credentials"}), 401


@app.route("/update-password", methods=["POST"])
def update_password():
    if "advisor_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    new_password = data.get("new_password")

    # Backend validation
    if not new_password or new_password.strip() == "":
        return jsonify({"message": "Password cannot be empty"}), 400

    is_valid, error_message = validate_password(new_password)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    # Generate new salt for the new password
    new_salt = os.urandom(16).hex()
    new_password_hash = hash_password(new_password, new_salt)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE
          public.user_credentials
        SET
          password_hash = %s,
          salt = %s
        WHERE
          user_id = %s
        """,
        (new_password_hash, new_salt, session["advisor_id"]),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Password updated"}), 200


@app.route("/client/<int:client_id>", methods=["GET"])
def get_client(client_id):
    if "advisor_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get specific client - any advisor can see any client
    cur.execute(
        """
        SELECT
          client_id,
          pgp_sym_decrypt(encrypted_clientname, %s) as clientname,
          pgp_sym_decrypt(encrypted_email, %s) as email,
          pgp_sym_decrypt(encrypted_password, %s) as password,
          created_on
        FROM
          public.client_credentials
        WHERE client_id = %s
        """,
        (ENCRYPTION_KEY, ENCRYPTION_KEY, ENCRYPTION_KEY, client_id),
    )

    client = cur.fetchone()
    cur.close()
    conn.close()

    if client:
        return jsonify({"client": client}), 200
    return jsonify({"message": "Client not found"}), 404


@app.route("/client/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    if "advisor_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    conn = get_db_connection()
    cur = conn.cursor()

    # Build update query dynamically based on provided fields
    update_fields = []
    params = []

    if "clientname" in data:
        update_fields.append("encrypted_clientname = pgp_sym_encrypt(%s, %s)")
        params.extend([data["clientname"], ENCRYPTION_KEY])

    if "email" in data:
        update_fields.append("encrypted_email = pgp_sym_encrypt(%s, %s)")
        params.extend([data["email"], ENCRYPTION_KEY])

    if "password" in data:
        update_fields.append("encrypted_password = pgp_sym_encrypt(%s, %s)")
        params.extend([data["password"], ENCRYPTION_KEY])

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    params.append(client_id)

    query = f"""
        UPDATE public.client_credentials
        SET {", ".join(update_fields)}
        WHERE client_id = %s
    """

    cur.execute(query, params)
    updated_rows = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated_rows > 0:
        return jsonify({"message": "Client updated"}), 200
    return jsonify({"message": "Client not found"}), 404


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

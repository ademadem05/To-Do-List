from flask import Flask, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import db
from auth import create_token, login_required

app = Flask(__name__)

db.init_db()

def validate_register(data):

    if not isinstance(data, dict):
        return["Request body must be a JSON object"]

    error = []
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(name,str) or not name.strip():
        error.append("'name' is required")
    if not isinstance(email,str) or '@' not in email:
        error.append("'email' must be a valid email address")
    if not isinstance(password,str) or len(password) < 8 :
        error.append("'password' must be at least 8 characters")

    return error

@app.route("/register", methods = ["POST"])
def register():
    data = request.get_json(silent=True)

    errors = validate_register(data=data)
    if errors:
        return jsonify({"errors": errors}), 400

    email = data["email"].strip().lower()

    password_hash = generate_password_hash(data["password"])

    user_id = db.create_user(data["name"], email, password_hash)

    if user_id is None:
        return jsonify({"message" : "Email is already registered"}), 409

    return jsonify({"token" : create_token(user_id)}), 201


@app.route("/login", methods = ["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data.get("email") or not data.get("password"):
        return jsonify({"message" : "Email and password are required"}), 400

    user = db.get_user_by_email(data.get("email").strip().lower())

    if user is None or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify({"message" : "invalid email or password"}), 401

    return jsonify({"token" : create_token(user["id"])}), 200

@app.route("/me", methods = ["GET"])
@login_required
def me():
    return jsonify({"user_id" : g.user_id}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"message" : "Not found"}), 404

def validate_todo(data):
    if not isinstance(data, dict):
        return ["Request body must be a JSON object"]

    errors = []
    title = data.get("title")
    description = data.get("description")

    if not isinstance(title, str) or not title.strip():
        errors.append("'title' is required and must be a non-empty string")
    if not isinstance(description, str):
        errors.append("'description' is required and must be a string")

    return errors

@app.route("/todos", methods=["POST"])
@login_required
def create_todo():
    data = request.get_json(silent= True)

    errors = validate_todo(data)
    if errors:
        return jsonify({"errors": errors}), 400
    todo = db.create_todo(g.user_id, data["title"].strip(), data["description"].strip())
    return jsonify(todo), 201


@app.route("/todos", methods=["GET"])
@login_required
def list_todos():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    term = request.args.get("term")

    page = max(page,1)
    limit = min(max(limit,1), 100)

    todos, total = db.get_todos(g.user_id, page, limit, term)

    return jsonify({
        "data": todos,
        "page": page,
        "limit": limit,
        "total": total,
    }), 200


@app.route("/todos/<int:todo_id>", methods=["PUT"])
@login_required
def update_todo(todo_id):
    todo = db.get_todo(todo_id)

    if todo is None:
        return jsonify({"message": "Todo not found"}), 404
    if todo["user_id"] != g.user_id:
        return jsonify({"message": "Forbidden"}), 403
    data = request.get_json(silent=True)
    errors = validate_todo(data)
    if errors:
        return jsonify({"errors": errors}), 400

    updated = db.update_todo(todo_id, data["title"].strip(), data["description"].strip())
    return jsonify(updated), 200


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
@login_required
def delete_todo(todo_id):
    # Silmeden önce aynı iki kontrol
    todo = db.get_todo(todo_id)
    if todo is None:
        return jsonify({"message": "Todo not found"}), 404
    if todo["user_id"] != g.user_id:
        return jsonify({"message": "Forbidden"}), 403

    db.delete_todo(todo_id)
    return "", 204



@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"message" : "Method not allowed"}), 405

if __name__ == "__main__":
    app.run(debug=True, port=5003)



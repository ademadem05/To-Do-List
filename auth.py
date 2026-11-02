import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import g, jsonify, request

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")

TOKEN_LIFETIME = timedelta(hours=1)

def create_token(user_id):
    payload = {
        "sub" : str(user_id),
        "exp" : datetime.now(timezone.utc) + TOKEN_LIFETIME
    }
    return jwt.encode(payload,SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({"message" : "Unauthorized"}), 401

        token = header[len("Bearer "):]
        user_id = decode_token(token)

        if user_id is None:
            return jsonify({"message" : "Unauthorized"}), 401

        g.user_id = user_id
        return f(*args, **kwargs)
    return wrapper
            

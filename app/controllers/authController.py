import uuid
import bcrypt
import jwt
import datetime
from instance.db import db
from flask import current_app

# Secret key for JWT (store in env in real apps)
JWT_SECRET = "your_secret_key_here"
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # 1 hour

def register_user(data):
    userName = data.get("userName")
    emailId = data.get("emailId")
    password = data.get("password")

    if not userName or not emailId or not password:
        return {"success": False, "error": "Username, EmailID and password required"}, 400

    # Check if user exists
    if emailId in db:
        return {"success": False, "error": "User already exists"}, 400

    # Hash password using bcrypt
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "userId": str(uuid.uuid4()),
        "userName": userName,
        "emailId": emailId,
        "password": hashed_pw.decode("utf-8"),
    }

    db.save(user_doc)

    return {"success": True, "message": "User registered successfully"}, 201


def login_user(data):
    userName = data.get("userName")
    password = data.get("password")

    try:
        user = db[userName]
    except KeyError:
        return {"success": False, "error": "Invalid username or password"}, 401

    # Verify password
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return {"success": False, "error": "Invalid username or password"}, 401

    # Generate JWT
    payload = {
        "userId": user["userId"],
        "userName": userName,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {"success": True, "token": token}, 200

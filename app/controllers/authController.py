import uuid
import bcrypt
import os
import jwt
from instance.db import db
from flask import current_app, jsonify, make_response
from datetime import datetime, timezone, timedelta

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

def register_user(data):
    userName = data.get("userName")
    emailId = data.get("emailId")
    password = data.get("password")

    if not userName or not emailId or not password:
        return {"success": False, "error": "Username, EmailID and password required"}, 400

    # Check if user exists (email as unique identifier assumed)
    if emailId in db:
        return {"success": False, "error": "User already exists"}, 400

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "userId": str(uuid.uuid4()),
        "userName": userName,
        "emailId": emailId,
        "password": hashed_pw.decode("utf-8"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    db.save(user_doc)

    # Create JWT
    token = jwt.encode(
        {
            "userId": user_doc["userId"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        },
        JWT_SECRET,
        ALGORITHM
    )

    # Create response + set cookie
    response = make_response(jsonify({
        "message": "User created successfully",
        "user": {
            "userId": user_doc["userId"],
            "userName": userName,
            "emailId": emailId
        },
        "token": token
    }), 201)

    response.set_cookie(
        "uid",
        token,
        httponly=True,
        secure=os.getenv("NODE_ENV") == "production",
        samesite="Strict",
        max_age=24 * 60 * 60  # 1 day
    )

    return response



def login_user(data):
    userName = data.get("userName")
    emailId = data.get("emailId")
    password = data.get("password")

    if not userName or not password or not emailId:
        return {"success": False, "error": "Username, EmailID and password required"}, 400

    try:
        user = db[emailId]
    except KeyError:
        return {"success": False, "error": "Invalid username or password"}, 401

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("utf-8")
    ):
        return {"success": False, "error": "Invalid username or password"}, 401

    # Create JWT
    token = jwt.encode(
        {
            "userId": user["userId"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        },
        JWT_SECRET,
        ALGORITHM
    )

    # Create response + set cookie
    response = make_response(jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "userId": user["userId"],
            "userName": user["userName"],
            "emailId": user["emailId"]
        },
        "token": token
    }), 200)

    response.set_cookie(
        "uid",
        token,
        httponly=True,
        secure=os.getenv("NODE_ENV") == "production",
        samesite="Strict",
        max_age=24 * 60 * 60  # 1 day
    )

    return response

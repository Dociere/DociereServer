import uuid
import bcrypt
import os
import jwt
from instance.db import userDB
from flask import current_app, jsonify, make_response
from datetime import datetime, timezone, timedelta
import time

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
start_time = time.time()


def register_user(data):
    userName = data.get("userName")
    emailId = data.get("emailId")
    password = data.get("password")

    if not userName or not emailId or not password:
        return {"success": False, "error": "Username, EmailID and password required"}, 400

    # Check if user exists (email as unique identifier assumed)
    if emailId in userDB:
        return {"success": False, "error": "User already exists"}, 400

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "_id": emailId,
        "userId": str(uuid.uuid4()),
        "userName": userName,
        "emailId": emailId,
        "password": hashed_pw.decode("utf-8"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    userDB.save(user_doc)

    # Create JWT
    token = jwt.encode(
        {
            "userId": user_doc["userId"],
            "userName": user_doc["userName"],
            "emailId": user_doc["emailId"],
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
        samesite="Lax",
        max_age=24 * 60 * 60  # 1 day
    )

    return response



def login_user(data):
    userName = data.get("userName")
    emailId = data.get("emailId")
    password = data.get("password")

    if not password or not emailId:
        return {"success": False, "error": "EmailID and password required"}, 400

    try:
        user = userDB[emailId]
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
            "userName": user["userName"],
            "emailId": user["emailId"],
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
        samesite="Lax",
        max_age=24 * 60 * 60  # 1 day
    )

    return response

def logout_user():
    response = make_response(jsonify({"success": True, "message": "Logged out successfully"}), 200)

    response.set_cookie("uid", "", httponly=True, samesite="Lax", max_age=0)
    return response


def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return {"userId": payload["userId"], "userName": payload["userName"], "emailId": payload["emailId"]}
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def check_auth_user(request):
    token = request.cookies.get("uid")
    if not token:
        return {"authenticated": False, "message": "No token"}, 401

    try:
        user_payload = decode_jwt(token)
        return {"authenticated": True, "user": user_payload}, 200
    except Exception as e:
        return {"authenticated": False, "message": str(e)}, 401


# def check_server_health():
#     return jsonify({
#         "status": "healthy",
#         "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
#         "uptime": time.time() - start_time
#     })
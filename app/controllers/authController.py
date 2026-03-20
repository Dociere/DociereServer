import uuid
import os
import jwt
import hashlib

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    print("⚠️  Warning: bcrypt not found. Using insecure hashlib fallback for development.")

from instance.db import userDB
from fastapi.responses import JSONResponse
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
        return JSONResponse(
            content={"success": False, "error": "Username, EmailID and password required"},
            status_code=400,
        )

    # Check if user exists (email as unique identifier assumed)
    result = list(userDB.find({"selector": {"emailId": emailId}}))
    if result:
        return JSONResponse(
            content={"success": False, "error": "User already exists"},
            status_code=400,
        )

    # Hash password
    if HAS_BCRYPT:
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    else:
        # INSECURE FALLBACK FOR DEV ONLY
        hashed_pw = hashlib.sha256(password.encode("utf-8")).hexdigest()

    user_id = str(uuid.uuid4())

    user_doc = {
        "_id": user_id,
        "userId": user_id,
        "userName": userName,
        "emailId": emailId,
        "password": hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    userDB.save(user_doc)

    # Create JWT
    token = jwt.encode(
        {
            "userId": user_doc["userId"],
            "userName": user_doc["userName"],
            "emailId": user_doc["emailId"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        },
        JWT_SECRET,
        ALGORITHM
    )

    # Create response + set cookie
    response = JSONResponse(
        content={
            "message": "User created successfully",
            "user": {
                "userId": user_doc["userId"],
                "userName": userName,
                "emailId": emailId
            },
            "token": token
        },
        status_code=201,
    )

    response.set_cookie(
        key="uid",
        value=token,
        httponly=True,
        secure=os.getenv("NODE_ENV") == "production",
        samesite="lax",
        max_age=24 * 60 * 60  # 1 day
    )

    return response



def login_user(data):
    emailId = data.get("emailId")
    password = data.get("password")

    if not password or not emailId:
        return JSONResponse(
            content={"success": False, "error": "EmailID and password required"},
            status_code=400,
        )

    try:
        result = userDB.find({"selector": {"emailId": emailId}})
        user = list(result)[0] if result else None
    except KeyError:
        return JSONResponse(
            content={"success": False, "error": "Invalid username or password"},
            status_code=401,
        )

    if HAS_BCRYPT:
        try:
            is_correct = bcrypt.checkpw(
                password.encode("utf-8"),
                user["password"].encode("utf-8")
            )
        except Exception:
            # Handle cases where existing DB has non-bcrypt hashes
            is_correct = user["password"] == hashlib.sha256(password.encode("utf-8")).hexdigest()
    else:
        is_correct = user["password"] == hashlib.sha256(password.encode("utf-8")).hexdigest()

    if not is_correct:
        return JSONResponse(
            content={"success": False, "error": "Invalid username or password"},
            status_code=401,
        )

    # Create JWT
    token = jwt.encode(
        {
            "userId": user["userId"],
            "userName": user["userName"],
            "emailId": user["emailId"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        },
        JWT_SECRET,
        ALGORITHM
    )

    # Create response + set cookie
    response = JSONResponse(
        content={
            "success": True,
            "message": "Login successful",
            "user": {
                "userId": user["userId"],
                "userName": user["userName"],
                "emailId": user["emailId"]
            },
            "token": token
        },
        status_code=200,
    )

    response.set_cookie(
        key="uid",
        value=token,
        httponly=True,
        secure=os.getenv("NODE_ENV") == "production",
        samesite="lax",
        max_age=24 * 60 * 60  # 1 day
    )

    return response

def logout_user():
    response = JSONResponse(
        content={"success": True, "message": "Logged out successfully"},
        status_code=200,
    )
    response.set_cookie(key="uid", value="", httponly=True, samesite="lax", max_age=0)
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
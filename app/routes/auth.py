from flask import Blueprint, request, jsonify
from app.controllers.authController import register_user, login_user, check_auth_user, logout_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def register():
    return register_user(request.get_json())

@auth_bp.route("/login", methods=["POST"])
def login():
    return login_user(request.get_json())

@auth_bp.route("/signout", methods=["POST"])
def logout():
    return logout_user()

@auth_bp.route("/check-auth", methods=["GET"])
def check_auth():
    response, status = check_auth_user(request)
    return jsonify(response), status
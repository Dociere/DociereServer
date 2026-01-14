from flask import Blueprint, request
from app.controllers.authController import register_user, login_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def register():
    return register_user(request.get_json())

@auth_bp.route("/login", methods=["POST"])
def login():
    return login_user(request.get_json())

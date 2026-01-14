from flask import Blueprint, request, jsonify
from app.controllers.authController import register_user, login_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def register():
    response, status = register_user(request.get_json())
    return jsonify(response), status

@auth_bp.route("/login", methods=["POST"])
def login():
    response, status = login_user(request.get_json())
    return jsonify(response), status

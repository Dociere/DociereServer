from flask import Blueprint, jsonify, request
from app.controllers.projectController import saveProject

project_bp = Blueprint("project", __name__)

@project_bp.route("/projects/<project_id>", methods=["PUT"])
def save_project(project_id ):
    return saveProject(project_id, request.get_json())
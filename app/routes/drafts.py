from flask import Blueprint, jsonify, request

from app.controllers.draftController import createDraft

draft_bp = Blueprint("draft", __name__)

@draft_bp.route("/drafts/<project_id>", methods=["PUT"])
def create_draft(project_id ):
    return createDraft(project_id, request.get_json())
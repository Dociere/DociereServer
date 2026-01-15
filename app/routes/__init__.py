from .latex import latex_bp
from .health import health_bp
from .auth import auth_bp
from .collaboration import collaboration_bp

def register_blueprints(app):
    app.register_blueprint(latex_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(collaboration_bp)
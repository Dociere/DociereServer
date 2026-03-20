from .latex import latex_router
from .health import health_router
from .auth import auth_router
from .collaboration import collaboration_router
from .project import project_router
from .equation import equation_router
from .drafts import draft_router
from .aiconfig import aiconfig_router
from .extensions import extensions_router

def get_routers():
    return [
        equation_router,
        latex_router,
        health_router,
        auth_router,
        project_router,
        draft_router,
        collaboration_router,
        aiconfig_router,
        extensions_router,
    ]
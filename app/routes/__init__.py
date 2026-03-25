from .latex import latex_router
from .health import health_router
from .auth import auth_router
from .collaboration import collaboration_router
from .project import project_router
from .equation import equation_router
from .drafts import draft_router
from .aiconfig import aiconfig_router
from .ai_chat import ai_chat_router
from .citation import citation_router

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
        ai_chat_router,
        citation_router,
    ]
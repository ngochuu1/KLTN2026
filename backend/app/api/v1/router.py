from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.workspace_invitations import router as workspace_invitations_router
from app.api.v1.channels import router as channels_router
from app.api.v1.chat import router as chat_router
from app.api.v1.chat_websocket import router as chat_websocket_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)

router.include_router(workspaces_router)
router.include_router(workspace_invitations_router)
router.include_router(channels_router)
router.include_router(chat_router)
router.include_router(chat_websocket_router)

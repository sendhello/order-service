from fastapi.routing import APIRouter
from security import ONLY_ADMIN, PROTECTED

from .auth import router as auth_router
from .google import router as google_router
from .profile import router as profile_router
from .roles import router as roles_router
from .users import router as users_router
from .verify import router as verify_router


router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(google_router, prefix="/google", tags=["Google Auth"])
router.include_router(verify_router, prefix="/verify", tags=["Verify"])
router.include_router(profile_router, prefix="/profile", tags=["Profile"], dependencies=PROTECTED)

router.include_router(users_router, prefix="/users", tags=["Users"], dependencies=ONLY_ADMIN)
router.include_router(roles_router, prefix="/roles", tags=["Roles"], dependencies=ONLY_ADMIN)

from fastapi import Depends

from .auth import admin_protected, full_protected, partial_protected, refresh_protected


PROTECTED = [Depends(full_protected)]
PART_PROTECTED = [Depends(partial_protected)]
REFRESH_PROTECTED = [Depends(refresh_protected)]
ONLY_ADMIN = [Depends(admin_protected)]

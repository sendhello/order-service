from fastapi import Depends

from .auth import protected


PROTECTED = [Depends(protected)]

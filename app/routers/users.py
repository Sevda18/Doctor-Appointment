from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.schemas.user import UserOut

router = APIRouter(prefix="", tags=["users"])

@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user

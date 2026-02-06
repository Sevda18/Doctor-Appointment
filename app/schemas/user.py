from pydantic import BaseModel
from typing import Optional

class UserOut(BaseModel):
    id: int
    email: Optional[str] = None
    username: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

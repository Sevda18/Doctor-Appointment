from pydantic import BaseModel

class SpecialtyOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SpecialtyCreate(BaseModel):
    name: str

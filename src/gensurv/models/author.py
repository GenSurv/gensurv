from pydantic import BaseModel


class Author(BaseModel):
    id: str | None
    name: str

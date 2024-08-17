from pydantic import BaseModel

from .author import Author


class Paper(BaseModel):
    id: str
    title: str
    abstract: str | None
    venue: str
    year: int
    authors: list[Author]

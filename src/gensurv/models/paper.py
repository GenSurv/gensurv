from pydantic import BaseModel

from .author import Author


class Paper(BaseModel):
    id: str
    title: str
    abstract: str | None
    venue: str | None
    year: int | None
    authors: list[Author] | None
    citation_styles: dict[str, str] | None

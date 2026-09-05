from pydantic import BaseModel, Field


class EpisodeCreate(BaseModel):
    episode_id: str = Field(min_length=1, max_length=50)
    season_id: int
    episode_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    duration_seconds: int | None = Field(default=None, ge=1)
    language: str = Field(min_length=1, max_length=10)
    content_group: str = Field(min_length=1, max_length=255)
    status: str = "draft"
    categories: list[str] = Field(default_factory=list)


class EpisodeUpdate(BaseModel):
    episode_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    duration_seconds: int | None = Field(default=None, ge=1)
    language: str | None = Field(default=None, min_length=1, max_length=10)
    content_group: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    categories: list[str] | None = None
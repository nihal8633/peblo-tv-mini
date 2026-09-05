from pydantic import BaseModel, ConfigDict


class ArtworkResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    episode_id: int
    slot: str
    object_key: str
    width: int
    height: int
    size_bytes: int
    content_type: str
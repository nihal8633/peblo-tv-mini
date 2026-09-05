from PIL import Image
from io import BytesIO

import pytest

from app.services.validation import validate_artwork


def make_image(
    width: int,
    height: int,
    image_format: str = "JPEG",
) -> bytes:
    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


def test_valid_poster():
    file_bytes = make_image(600, 900)

    result = validate_artwork(
        slot="poster",
        file_bytes=file_bytes,
        content_type="image/jpeg",
    )

    assert result["width"] == 600
    assert result["height"] == 900
    assert result["content_type"] == "image/jpeg"


def test_invalid_poster_dimensions():
    file_bytes = make_image(500, 900)

    with pytest.raises(ValueError, match="Invalid poster dimensions"):
        validate_artwork(
            slot="poster",
            file_bytes=file_bytes,
            content_type="image/jpeg",
        )


def test_invalid_artwork_slot():
    file_bytes = make_image(600, 900)

    with pytest.raises(
        ValueError,
        match="Invalid artwork slot",
    ):
        validate_artwork(
            slot="unknown",
            file_bytes=file_bytes,
            content_type="image/jpeg",
        )


def test_invalid_file_type():
    file_bytes = make_image(600, 900)

    with pytest.raises(
        ValueError,
        match="Invalid file type",
    ):
        validate_artwork(
            slot="poster",
            file_bytes=file_bytes,
            content_type="text/plain",
        )


def test_invalid_image_bytes():
    with pytest.raises(
        ValueError,
        match="not a valid image",
    ):
        validate_artwork(
            slot="poster",
            file_bytes=b"not an image",
            content_type="image/jpeg",
        )
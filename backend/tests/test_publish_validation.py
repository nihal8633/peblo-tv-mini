from app.models import Artwork, Episode, Season, Show
from app.services.publish import validate_for_publish


def create_show(
    db,
    slug: str,
    section: str = "series",
):
    show = Show(
        slug=slug,
        title=f"Test Show {slug}",
        synopsis="Test synopsis",
        section=section,
        status="published",
    )

    db.add(show)
    db.flush()

    return show


def create_season(
    db,
    show_id: int,
    season_number: int,
):
    season = Season(
        show_id=show_id,
        season_number=season_number,
    )

    db.add(season)
    db.flush()

    return season


def create_episode(
    db,
    season_id: int,
    episode_id: str,
    content_group: str,
    language: str = "en",
    duration_seconds: int | None = 120,
):
    episode = Episode(
        episode_id=episode_id,
        season_id=season_id,
        episode_number=1,
        title="Test Episode",
        duration_seconds=duration_seconds,
        language=language,
        content_group=content_group,
        status="published",
        categories=["stories"],
    )

    db.add(episode)
    db.flush()

    return episode


def add_complete_artwork(
    db,
    episode_id: int,
):
    artwork_dimensions = {
        "poster": (600, 900),
        "banner": (1280, 720),
        "thumbnail": (640, 360),
    }

    for slot, (width, height) in artwork_dimensions.items():
        artwork = Artwork(
            episode_id=episode_id,
            slot=slot,
            object_key=(
                f"test/{episode_id}/{slot}.jpg"
            ),
            width=width,
            height=height,
            size_bytes=1024,
            content_type="image/jpeg",
        )

        db.add(artwork)

    db.flush()


def test_valid_published_episode_passes(db_session):
    show = create_show(
        db_session,
        "publish-validation-valid",
    )

    season = create_season(
        db_session,
        show.id,
        1,
    )

    episode = create_episode(
        db_session,
        season.id,
        "test-publish-valid",
        "test-group-valid",
    )

    add_complete_artwork(
        db_session,
        episode.id,
    )

    errors = validate_for_publish(db_session)

    matching_errors = [
        error
        for error in errors
        if "test-publish-valid" in error
    ]

    assert matching_errors == []


def test_published_episode_without_duration_fails(
    db_session,
):
    show = create_show(
        db_session,
        "publish-validation-duration",
    )

    season = create_season(
        db_session,
        show.id,
        1,
    )

    episode = create_episode(
        db_session,
        season.id,
        "test-publish-no-duration",
        "test-group-no-duration",
        duration_seconds=None,
    )

    add_complete_artwork(
        db_session,
        episode.id,
    )

    errors = validate_for_publish(db_session)

    matching_errors = [
        error
        for error in errors
        if "test-publish-no-duration" in error
    ]

    assert any(
        "no valid duration" in error
        for error in matching_errors
    )


def test_published_episode_missing_artwork_fails(
    db_session,
):
    show = create_show(
        db_session,
        "publish-validation-artwork",
    )

    season = create_season(
        db_session,
        show.id,
        1,
    )

    episode = create_episode(
        db_session,
        season.id,
        "test-publish-no-artwork",
        "test-group-no-artwork",
    )

    errors = validate_for_publish(db_session)

    matching_errors = [
        error
        for error in errors
        if "test-publish-no-artwork" in error
    ]

    assert any(
        "missing artwork" in error
        for error in matching_errors
    )


def test_season_zero_is_excluded_from_validation(
    db_session,
):
    show = create_show(
        db_session,
        "publish-validation-season-zero",
    )

    season = create_season(
        db_session,
        show.id,
        0,
    )

    create_episode(
        db_session,
        season.id,
        "test-season-zero",
        "test-group-season-zero",
        duration_seconds=None,
    )

    errors = validate_for_publish(db_session)

    matching_errors = [
        error
        for error in errors
        if "test-season-zero" in error
    ]

    assert matching_errors == []
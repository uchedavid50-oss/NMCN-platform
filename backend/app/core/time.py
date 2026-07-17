from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (no tzinfo attached).

    datetime.utcnow() is deprecated, but switching straight to
    datetime.now(timezone.utc) everywhere would make every timestamp
    timezone-aware — and every DateTime column in this app is naive
    (`DateTime()`, not `DateTime(timezone=True)`). Mixing aware and naive
    datetimes silently causes comparison bugs, which is exactly the class
    of timezone mistake that broke the mock-exam countdown timer back in
    Module 11 (JS side that time, not Python — same category of bug).

    This helper keeps the output identical to the old datetime.utcnow()
    (naive, UTC) while using the non-deprecated API underneath. If this
    app ever moves to timezone-aware columns throughout, this is the one
    place that would need to change.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

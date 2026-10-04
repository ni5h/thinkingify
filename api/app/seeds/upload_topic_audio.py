"""Upload the curated topic narration audio to Supabase Storage.

One-time step after the app is pointed at a new Supabase project: pushes every
file in `topic_audio/` to `<bucket>/topic-audio/<filename>` so the `audio_url`
values seeded by `topics.py` resolve. Idempotent (upserts). Needs a service-role
key in the environment (SUPABASE_SERVICE_ROLE_KEY) and the target bucket to
already exist as a public bucket. Run standalone:

    python -m app.seeds.upload_topic_audio
"""

from pathlib import Path

from supabase import create_client

from app.core.config import settings

_AUDIO_DIR = Path(__file__).parent / "topic_audio"
_DEST_PREFIX = "topic-audio"


def main() -> None:
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    if not key:
        raise SystemExit("No Supabase key configured (SUPABASE_SERVICE_ROLE_KEY).")
    client = create_client(settings.supabase_url, key)
    bucket = client.storage.from_(settings.supabase_storage_bucket)

    files = sorted(_AUDIO_DIR.glob("*.mpeg"))
    uploaded = 0
    for f in files:
        dest = f"{_DEST_PREFIX}/{f.name}"
        bucket.upload(
            dest,
            f.read_bytes(),
            {"content-type": "audio/mpeg", "upsert": "true"},
        )
        uploaded += 1
    print(f"Uploaded {uploaded} audio file(s) to {settings.supabase_storage_bucket}/{_DEST_PREFIX}/")


if __name__ == "__main__":
    main()

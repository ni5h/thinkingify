from app.pipeline.adapters.embeddings import HashEmbeddingAdapter
from app.pipeline.dedupe import dedupe
from app.pipeline.types import GeneratedItem


def _item(body: str) -> GeneratedItem:
    return GeneratedItem(kind="recall", body=body, options=["a", "b"], answer="a", hint="", difficulty=1)


def test_near_duplicates_dropped_first_kept():
    items = [
        _item("the three lives in the tens house"),
        _item("the three lives in the tens house"),  # exact dup
        _item("cats sleep on warm sunny windowsills"),
    ]
    kept, dropped = dedupe(items, reference_texts=[], adapter=HashEmbeddingAdapter(), threshold=0.9)
    assert len(kept) == 2 and len(dropped) == 1
    assert dropped[0] is items[1]  # the later duplicate is dropped, the first kept
    assert all(it.dedupe_score is not None for it in items)


def test_match_against_reference_set_is_dropped():
    items = [_item("the three lives in the tens house")]
    kept, dropped = dedupe(
        items,
        reference_texts=["the three lives in the tens house"],
        adapter=HashEmbeddingAdapter(),
        threshold=0.9,
    )
    assert kept == [] and len(dropped) == 1
    assert dropped[0].dedupe_score >= 0.9


def test_distinct_items_kept_and_threshold_respected():
    items = [_item("alpha beta gamma delta"), _item("penguins waddle across antarctic ice")]
    kept, dropped = dedupe(items, reference_texts=[], adapter=HashEmbeddingAdapter(), threshold=0.9)
    assert len(kept) == 2 and dropped == []

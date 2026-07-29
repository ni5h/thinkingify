from app.services.fact_leak_guard import is_fact_leak

_EXPLAINER = (
    "Owls can rotate their heads almost all the way around because they "
    "have extra vertebrae in their necks and special blood vessels that "
    "keep blood flowing even when the neck is twisted."
)


def test_verbatim_recitation_is_flagged():
    reply = "Well, owls have extra vertebrae in their necks and special blood vessels that keep blood flowing."
    assert is_fact_leak(reply, _EXPLAINER) is True


def test_unrelated_clean_reply_is_not_flagged():
    reply = "What part of the story are you most excited to write about first?"
    assert is_fact_leak(reply, _EXPLAINER) is False


def test_short_reply_is_never_flagged():
    assert is_fact_leak("Neat!", _EXPLAINER) is False


def test_paraphrased_fact_is_not_caught_known_limitation():
    # Documented limitation: a fact restated in different words has no
    # word-overlap with the source, so the cheap mechanical check can't
    # see it. This test exists to make that limitation explicit and
    # regression-visible, not to claim it's desirable.
    reply = "Birds like this one can turn their neck a huge amount thanks to bones that give them extra room to twist."
    assert is_fact_leak(reply, _EXPLAINER) is False


def test_none_and_empty_sources_are_skipped_without_error():
    assert is_fact_leak("Some perfectly normal reply text here today.", None, "") is False


def test_multiple_sources_checked():
    transcript = "The secret is a special bone structure unlike anything else in the animal kingdom."
    reply = "It's a special bone structure unlike anything else in the animal kingdom, right?"
    assert is_fact_leak(reply, _EXPLAINER, transcript) is True

from app.pipeline import maths
from app.pipeline.precheck import run_prechecks
from app.pipeline.types import GeneratedItem


class FakeCritique:
    """Second-model stand-in: returns the option indices it's told to."""

    name = "fake-critique"

    def __init__(self, indices):
        self._indices = indices

    async def generate(self, *, system, prompt, tool):
        return {"correct_option_indices": self._indices}


def _correct_index(item: GeneratedItem) -> int:
    return item.options.index(item.answer)


async def test_clean_maths_item_passes_all_checks():
    it = maths.generate_items(n=1, seed=3)[0]
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([_correct_index(it)]), reading_grade_max=8.0, dedupe_threshold=0.9
    )
    assert failures == []


async def test_recompute_and_answer_in_options_both_catch_a_bad_maths_answer():
    it = maths.generate_items(n=1, seed=3)[0]
    it.answer = "999,999"  # not recomputable and not an option
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([0]), reading_grade_max=8.0, dedupe_threshold=0.9
    )
    checks = {f.check for f in failures}
    assert "maths_recompute" in checks
    assert "answer_in_options" in checks


async def test_reading_level_too_high_is_rejected():
    it = GeneratedItem(
        kind="apply",
        body="The indefatigable protagonist's circumlocutory soliloquy utterly bewildered the consternated interlocutors.",
        options=["yes", "no"],
        answer="yes",
        hint="",
        difficulty=3,
    )
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([0]), reading_grade_max=5.0, dedupe_threshold=0.9
    )
    assert any(f.check == "reading_level" for f in failures)


async def test_ambiguous_critique_is_rejected():
    it = GeneratedItem(kind="apply", body="Pick a.", options=["a", "b"], answer="a", hint="", difficulty=1)
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([0, 1]), reading_grade_max=8.0, dedupe_threshold=0.9
    )
    assert any(f.check == "critique_ambiguous" for f in failures)


async def test_critique_disagreeing_with_our_answer_is_rejected():
    it = GeneratedItem(kind="apply", body="Pick a.", options=["a", "b"], answer="a", hint="", difficulty=1)
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([1]), reading_grade_max=8.0, dedupe_threshold=0.9
    )
    assert any(f.check == "critique_mismatch" for f in failures)


async def test_dedupe_score_over_threshold_is_rejected():
    it = GeneratedItem(kind="apply", body="Pick a.", options=["a", "b"], answer="a", hint="", difficulty=1)
    it.dedupe_score = 0.95
    failures = await run_prechecks(
        it, critique_adapter=FakeCritique([0]), reading_grade_max=8.0, dedupe_threshold=0.9
    )
    assert any(f.check == "dedupe" for f in failures)

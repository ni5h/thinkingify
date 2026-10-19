from app.pipeline import maths


def test_every_generated_answer_recomputes_and_is_an_option():
    items = maths.generate_items(band=2, n=16, seed=7)
    assert len(items) == 16
    for it in items:
        assert it.template_id, "maths items must carry a template for recompute"
        assert maths.recompute(it) == it.answer
        assert it.answer in it.options
        assert len(it.options) == len(set(it.options)), "options must be distinct"


def test_generation_is_deterministic_for_a_seed():
    a = [(i.body, i.answer) for i in maths.generate_items(n=8, seed=11)]
    b = [(i.body, i.answer) for i in maths.generate_items(n=8, seed=11)]
    assert a == b


def test_templates_rotate_so_a_session_is_varied():
    kinds = {it.template_id for it in maths.generate_items(n=4, seed=3)}
    assert kinds == {"digit_worth", "expanded_form", "compare", "build_biggest"}


def test_recompute_catches_a_corrupted_answer():
    it = maths.generate_items(n=1, seed=1)[0]
    it.answer = "0"
    assert maths.recompute(it) != it.answer

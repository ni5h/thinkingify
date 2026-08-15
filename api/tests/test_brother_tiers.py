from app.services import brother_tiers
from app.services.brother_tiers import BROTHER_TIERS, TIERS_BY_ID, brother, generate_number, next_tier_id


def test_brother_math():
    assert brother(7, 10) == 3
    assert brother(47, 10) == 3
    assert brother(57, 100) == 43
    assert brother(343, 100) == 57
    assert brother(657, 1000) == 343
    assert brother(2657, 1000) == 343
    # A number already on a multiple returns 0.
    assert brother(300, 100) == 0
    assert brother(50, 10) == 0


def test_next_tier_id_walks_the_chain_and_stops():
    assert next_tier_id("B1") == "B2"
    assert next_tier_id("B5") == "B6"
    assert next_tier_id("B6") is None


def test_generation_stays_in_range_and_excludes_zero_result_for_entry_tiers():
    for tier in BROTHER_TIERS:
        for _ in range(200):
            n = generate_number(tier)
            assert tier.min_n <= n <= tier.max_n
            if not tier.allow_zero_result:
                assert brother(n, tier.power) != 0


def test_generation_excludes_immediate_repeat():
    tier = TIERS_BY_ID["B4"]
    prev = generate_number(tier)
    for _ in range(200):
        n = generate_number(tier, avoid=prev)
        assert n != prev
        prev = n


def test_b4_b6_vary_the_inert_prefix():
    # Across many generations avoiding the previous number, an isolate tier
    # should not keep producing the same leading digit(s).
    tier = TIERS_BY_ID["B4"]
    prefixes = set()
    prev = None
    for _ in range(50):
        n = generate_number(tier, avoid=prev)
        prefixes.add(brother_tiers._inert_prefix(n, tier))
        prev = n
    assert len(prefixes) > 1


def test_active_digits_config_matches_spec():
    # Only B4/B6 isolate a trailing group narrower than the number width.
    assert TIERS_BY_ID["B4"].active_digits == 2  # of a 3-digit number
    assert TIERS_BY_ID["B6"].active_digits == 3  # of a 4-digit number
    assert TIERS_BY_ID["B2"].active_digits == 2  # whole 2-digit shown

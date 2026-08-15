import random
from dataclasses import dataclass

# The "Brothers" tier config. A brother of a number is its complement to
# the next power of 10 (7->3, 47->3, 57->43, 657->343). Config-as-data,
# same convention as grammar_concepts / sentence_framing_concepts — a new
# tier ("lakh brother", etc.) is a one-line addition here, no logic change.


@dataclass(frozen=True)
class BrotherTier:
    id: str
    name: str
    power: int  # complement to the next multiple of this (10 / 100 / 1000)
    min_n: int
    max_n: int
    # How many trailing digits are visually "active" (the isolate-the-chunk
    # teaching, spec §4.3). Only tiers where this is fewer than the number's
    # width get their inert prefix de-emphasized — i.e. B4 and B6.
    active_digits: int
    # Whether a 0-result question (number already a multiple of `power`) is
    # allowed. Excluded for the entry tiers (B1-B3), allowed once the
    # concept is solid (B4+), per spec §2/§5.
    allow_zero_result: bool
    prerequisite: str | None


BROTHER_TIERS: list[BrotherTier] = [
    BrotherTier("B1", "Decade brother, single digit", 10, 1, 9, 1, False, None),
    BrotherTier("B2", "Decade brother, 2-digit", 10, 10, 99, 2, False, "B1"),
    BrotherTier("B3", "Century brother, 2-digit", 100, 1, 99, 2, False, "B2"),
    BrotherTier("B4", "Century brother, 3-digit", 100, 100, 999, 2, True, "B3"),
    BrotherTier("B5", "Kilo brother, 3-digit", 1000, 1, 999, 3, False, "B4"),
    BrotherTier("B6", "Kilo brother, 4-digit", 1000, 1000, 9999, 3, True, "B5"),
]

TIERS_BY_ID: dict[str, BrotherTier] = {t.id: t for t in BROTHER_TIERS}
TIER_ORDER: list[str] = [t.id for t in BROTHER_TIERS]

ENTRY_TIER_ID = TIER_ORDER[0]


def brother(n: int, power: int) -> int:
    """Complement of n to the next multiple of `power`. A number already on
    a multiple returns 0 (e.g. brother(300, 100) == 0)."""
    return (power - n % power) % power


def next_tier_id(tier_id: str) -> str | None:
    idx = TIER_ORDER.index(tier_id)
    return TIER_ORDER[idx + 1] if idx + 1 < len(TIER_ORDER) else None


def generate_number(tier: BrotherTier, avoid: int | None = None) -> int:
    """Pick a uniform-random in-range number, excluding a 0-result (unless
    the tier allows it) and the immediately-preceding number. For the
    isolate tiers (B4/B6) also vary the inert prefix so the child can't
    pattern-match a fixed leading digit."""
    prev_prefix = _inert_prefix(avoid, tier) if avoid is not None else None
    for _ in range(100):
        n = random.randint(tier.min_n, tier.max_n)
        if n == avoid:
            continue
        if not tier.allow_zero_result and brother(n, tier.power) == 0:
            continue
        if prev_prefix is not None and tier.active_digits < _digit_count(n) and _inert_prefix(n, tier) == prev_prefix:
            continue
        return n
    # Fallback after an unlucky run of rejects — take the first acceptable
    # number deterministically rather than loop forever.
    for n in range(tier.min_n, tier.max_n + 1):
        if n != avoid and (tier.allow_zero_result or brother(n, tier.power) != 0):
            return n
    return tier.min_n


def _digit_count(n: int) -> int:
    return len(str(n))


def _inert_prefix(n: int, tier: BrotherTier) -> int | None:
    """The leading (inert) digits for an isolate tier, or None when the
    whole number is active."""
    if tier.active_digits >= _digit_count(n):
        return None
    return n // (10**tier.active_digits)

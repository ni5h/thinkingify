"""Seed a starter set of 4th-grade olympiad-style maths problems.

Idempotent (skips a problem whose slug already exists) and authored under
the dev-login user (creating it if absent). Run standalone:

    python -m app.seeds.math_problems

This is the "hand-entered problems" content for Phase 1 — enough real,
mentally-solvable, pattern/reasoning-flavoured problems to try the
coached-solving loop before the admin editor (1b) or book-scanning
(Phase 3) exist. Every problem has a clean answer and a short, elegant
worked solution (the coach's private context + the post-solve reveal).
"""

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.math_problem import MathAnswerKind, MathProblem, MathProblemStatus
from app.models.user import User, UserRole
from app.services.auth_service import DEV_USER_EMAIL, DEV_USER_GOOGLE_SUB, DEV_USER_NAME

# (title, statement, answer, answer_kind, solution, concept_tags, difficulty)
_PROBLEMS = [
    (
        "The growing gaps",
        "What number comes next in this pattern?\n\n**2, 6, 12, 20, 30, ___**",
        "42",
        MathAnswerKind.integer,
        "Look at the gaps between the numbers: 4, 6, 8, 10 — they grow by 2 each time. "
        "So the next gap is 12, and 30 + 12 = **42**.",
        ["patterns", "sequences"],
        1,
    ),
    (
        "Clever adding",
        "Add these four numbers in the smartest way you can:\n\n**25 + 26 + 27 + 28**",
        "106",
        MathAnswerKind.integer,
        "Pair them from the outside in: 25 + 28 = 53, and 26 + 27 = 53. "
        "Two 53s make **106** — no need to add one at a time.",
        ["mental-maths", "grouping"],
        1,
    ),
    (
        "The mystery number",
        "I'm thinking of a number. If I double it and then add 5, I get 17. "
        "What is my number?",
        "6",
        MathAnswerKind.integer,
        "Work backwards. Undo the +5: 17 − 5 = 12. Then undo the doubling: 12 ÷ 2 = **6**.",
        ["working-backwards", "logic"],
        2,
    ),
    (
        "Outfits",
        "You have **3 shirts** and **2 pairs of shorts**. Wearing one shirt and one pair "
        "of shorts, how many different outfits can you make?",
        "6",
        MathAnswerKind.integer,
        "Each of the 3 shirts can go with either of the 2 shorts, so 3 × 2 = **6** outfits.",
        ["counting", "combinatorics"],
        2,
    ),
    (
        "Rabbit numbers",
        "In this pattern, each number is the sum of the two before it:\n\n"
        "**1, 1, 2, 3, 5, 8, ___**\n\nWhat comes next?",
        "13",
        MathAnswerKind.integer,
        "Add the last two numbers: 5 + 8 = **13**. (This famous pattern is called the "
        "Fibonacci sequence.)",
        ["patterns", "sequences"],
        1,
    ),
    (
        "Cinema seats",
        "A small cinema has **8 rows** with **12 seats** in each row. "
        "How many seats are there in total?",
        "96",
        MathAnswerKind.integer,
        "8 × 12 is easier if you split the 12: 8 × 10 = 80 and 8 × 2 = 16, so 80 + 16 = **96**.",
        ["mental-maths", "multiplication"],
        2,
    ),
    (
        "The handshakes",
        "**4 friends** are at a party. Every friend shakes hands with every other friend "
        "exactly once. How many handshakes happen in total?",
        "6",
        MathAnswerKind.integer,
        "Count without repeating: the 1st friend shakes 3 hands, the 2nd has 2 new people "
        "left, the 3rd has 1. So 3 + 2 + 1 = **6** handshakes.",
        ["counting", "combinatorics", "logic"],
        3,
    ),
    (
        "Triangle of dots",
        "Dots are arranged in triangles that grow like this:\n\n"
        "**1, 3, 6, 10, ___**\n\nHow many dots are in the next triangle?",
        "15",
        MathAnswerKind.integer,
        "Each new triangle adds one more row of dots than the one before. The rows added "
        "are 2, 3, 4, then 5 — so 10 + 5 = **15**. (These are called triangular numbers.)",
        ["patterns", "sequences"],
        2,
    ),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        author = (
            await db.execute(select(User).where(User.google_sub == DEV_USER_GOOGLE_SUB))
        ).scalar_one_or_none()
        if author is None:
            author = User(
                id=uuid.uuid4(),
                google_sub=DEV_USER_GOOGLE_SUB,
                email=DEV_USER_EMAIL,
                name=DEV_USER_NAME,
                role=UserRole.learner,
            )
            db.add(author)
            await db.commit()
            await db.refresh(author)

        created = 0
        for order, (title, statement, answer, kind, solution, tags, difficulty) in enumerate(_PROBLEMS):
            from slugify import slugify

            slug = slugify(title)
            exists = (
                await db.execute(select(MathProblem.id).where(MathProblem.slug == slug))
            ).scalar_one_or_none()
            if exists is not None:
                continue
            db.add(
                MathProblem(
                    id=uuid.uuid4(),
                    title=title,
                    slug=slug,
                    statement_markdown=statement,
                    answer=answer,
                    answer_kind=kind,
                    solution_markdown=solution,
                    concept_tags=tags,
                    difficulty=difficulty,
                    status=MathProblemStatus.published,
                    order_index=order,
                    author_id=author.id,
                )
            )
            created += 1
        await db.commit()
        print(f"Seeded {created} new maths problem(s) ({len(_PROBLEMS) - created} already present).")


if __name__ == "__main__":
    asyncio.run(seed())

from pathlib import Path

from app.pipeline.ingest import OcrPage, build_outline, heading_candidates

# Original synthetic page text (not from any book) with a mix of headings,
# sentences, and page noise.
SAMPLE = """Chapter 5
What Animals Eat

Some animals eat only plants, so we call them herbivores and they graze all day.
A cow chews grass in the field.

Plant Eaters
Meat Eaters
Teeth And Food

Page 42
"""


def test_heading_candidates_keeps_titles_drops_sentences_and_noise():
    headings = heading_candidates(SAMPLE)
    assert "What Animals Eat" in headings
    assert "Plant Eaters" in headings
    assert "Teeth And Food" in headings
    # a full sentence is not a heading
    assert not any("chews grass" in h.lower() for h in headings)
    assert not any("herbivores" in h.lower() for h in headings)
    # page numbers filtered out
    assert "Page 42" not in headings
    assert "42" not in headings


def test_heading_candidates_dedupes():
    headings = heading_candidates("Water Cycle\nWater Cycle\nWATER CYCLE\n")
    assert len(headings) == 1


def test_build_outline_lists_topics_and_states_local_only():
    outline = build_outline([OcrPage(image=Path("p1.png"), text=SAMPLE)])
    assert "## Candidate topics" in outline
    assert "- What Animals Eat" in outline
    assert "Nothing here was sent to a model" in outline


def test_build_outline_handles_pages_with_no_headings():
    prose = OcrPage(image=Path("p.png"), text="only flowing sentences here, and nothing that looks like a title at all.")
    outline = build_outline([prose])
    assert "none detected" in outline

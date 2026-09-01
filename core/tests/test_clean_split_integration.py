from core.services.clean import clean_markdown
from core.services.split import split_sentences


class TestCleanIntoSplitPPTX:
    def test_three_bullets_stay_separate_after_clean(self):
        raw = (
            "- Cells are the basic unit of life\n"
            "- Mitochondria produce ATP\n"
            "- Chloroplasts perform photosynthesis"
        )
        cleaned = clean_markdown(raw, source_format="pptx")
        result = split_sentences(cleaned, source_format="pptx")
        assert result == [
            "Cells are the basic unit of life",
            "Mitochondria produce ATP",
            "Chloroplasts perform photosynthesis",
        ]

    def test_numbered_list_stays_separate_after_clean(self):
        raw = "1. Cells divide\n2. Cells differentiate\n3. Cells die"
        cleaned = clean_markdown(raw, source_format="pptx")
        result = split_sentences(cleaned, source_format="pptx")
        assert result == ["Cells divide", "Cells differentiate", "Cells die"]

    def test_bullet_wrapped_across_lines_still_rejoins_after_clean(self):
        raw = (
            "- Mitochondria are membrane-bound organelles that\n"
            "generate most of the cell's ATP supply"
        )
        cleaned = clean_markdown(raw, source_format="pptx")
        result = split_sentences(cleaned, source_format="pptx")
        assert result == [
            "Mitochondria are membrane-bound organelles that generate most of the cell's ATP supply"
        ]

    def test_pdf_path_is_unaffected_by_this_change(self):
        raw = "The mitochondria is the\npowerhouse of the cell."
        cleaned = clean_markdown(raw, source_format="pdf")
        result = split_sentences(cleaned, source_format="pdf")
        assert result == ["The mitochondria is the powerhouse of the cell."]

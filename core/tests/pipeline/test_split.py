from core.services.split import split_sentences


class TestSplitSentencesPDF:
    def test_abbreviation_does_not_split(self):
        text = "Dr. Smith discovered polonium."
        result = split_sentences(text, source_format="pdf")
        assert result == ["Dr. Smith discovered polonium."]

    def test_decimal_number_does_not_split(self):
        text = "The value is 3.14 in this case."
        result = split_sentences(text, source_format="pdf")
        assert result == ["The value is 3.14 in this case."]

    def test_multiple_sentences_on_one_line(self):
        text = "Cells divide. Mitosis has four phases."
        result = split_sentences(text, source_format="pdf")
        assert result == ["Cells divide.", "Mitosis has four phases."]

    def test_mid_sentence_line_wrap_rejoined(self):
        text = "The mitochondria is the\npowerhouse of the cell."
        result = split_sentences(text, source_format="pdf")
        assert result == ["The mitochondria is the powerhouse of the cell."]

    def test_terminal_punctuation_not_joined_to_next(self):
        text = "Cells divide.\nMitosis has four phases."
        result = split_sentences(text, source_format="pdf")
        assert result == ["Cells divide.", "Mitosis has four phases."]

    def test_empty_input_returns_empty_list(self):
        assert split_sentences("", source_format="pdf") == []
        assert split_sentences("   ", source_format="pdf") == []
        assert split_sentences("\n\n\n", source_format="pdf") == []

    def test_single_sentence_no_trailing_punctuation(self):
        text = "Final sentence"
        result = split_sentences(text, source_format="pdf")
        assert result == ["Final sentence"]

    def test_blank_lines_filtered_out(self):
        text = "First paragraph.\n\n\nSecond paragraph."
        result = split_sentences(text, source_format="pdf")
        assert result == ["First paragraph.", "Second paragraph."]

    def test_handles_initialisms(self):
        text = "The U.S. government funded the research."
        result = split_sentences(text, source_format="pdf")
        assert result == ["The U.S. government funded the research."]

    def test_handles_ellipsis(self):
        text = "Wait... what happened?"
        result = split_sentences(text, source_format="pdf")
        assert result == ["Wait... what happened?"]

    def test_mixed_wrapping_and_complete_sentences(self):
        text = "The mitochondria is the\npowerhouse of the cell.\n\nCells divide. Mitosis occurs."
        result = split_sentences(text, source_format="pdf")
        assert "The mitochondria is the powerhouse of the cell." in result
        assert "Cells divide." in result
        assert "Mitosis occurs." in result


class TestSplitSentencesPPTX:
    def test_simple_bullets_no_terminal_punctuation(self):
        text = (
            "Introduction to Cell Biology\n\n"
            "- Cells are the basic unit of life\n"
            "- Mitochondria produce ATP\n"
            "- Chloroplasts perform photosynthesis\n"
            "- Both organelles have their own DNA"
        )
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Introduction to Cell Biology",
            "Cells are the basic unit of life",
            "Mitochondria produce ATP",
            "Chloroplasts perform photosynthesis",
            "Both organelles have their own DNA",
        ]

    def test_bullets_with_mixed_terminal_punctuation(self):
        text = (
            "- Mitochondria produce ATP.\n"
            "- Chloroplasts perform photosynthesis\n"
            "- Both organelles have their own DNA."
        )
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Mitochondria produce ATP.",
            "Chloroplasts perform photosynthesis",
            "Both organelles have their own DNA.",
        ]

    def test_bullet_dash_prefix_is_stripped_or_preserved_consistently(self):
        text = "- Cells divide through mitosis"
        result = split_sentences(text, source_format="pptx")
        assert result == ["Cells divide through mitosis"]

    def test_bullet_containing_two_sentences_still_splits(self):
        text = "- Cells divide through mitosis. They also undergo apoptosis."
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Cells divide through mitosis.",
            "They also undergo apoptosis.",
        ]

    def test_slide_title_plus_bullets(self):
        text = "Photosynthesis\n\n- Occurs in chloroplasts\n- Produces glucose"
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Photosynthesis",
            "Occurs in chloroplasts",
            "Produces glucose",
        ]

    def test_empty_bullet_lines_are_skipped(self):
        text = "- Cells are alive\n-\n- DNA carries genetic information"
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Cells are alive",
            "DNA carries genetic information",
        ]

    def test_multiple_consecutive_blank_lines_between_bullets(self):
        text = "- First point\n\n\n\n- Second point"
        result = split_sentences(text, source_format="pptx")
        assert result == ["First point", "Second point"]

    def test_single_word_bullet(self):
        text = "- ATP"
        result = split_sentences(text, source_format="pptx")
        assert result == ["ATP"]

    def test_numbered_list_format(self):
        text = "1. Cells divide\n2. Cells differentiate\n3. Cells die"
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Cells divide",
            "Cells differentiate",
            "Cells die",
        ]

    def test_bullet_ending_in_colon_acts_as_its_own_line(self):
        text = "Key organelles:\n- Mitochondria\n- Chloroplast"
        result = split_sentences(text, source_format="pptx")
        assert result == ["Key organelles:", "Mitochondria", "Chloroplast"]

    def test_bullet_with_internal_abbreviation_not_split_mid_bullet(self):
        text = "- Dr. Smith discovered the enzyme in 1985"
        result = split_sentences(text, source_format="pptx")
        assert result == ["Dr. Smith discovered the enzyme in 1985"]

    def test_bullet_wrapped_across_lines_by_markitdown(self):
        text = "- Mitochondria are membrane-bound organelles that\ngenerate most of the cell's ATP supply"
        result = split_sentences(text, source_format="pptx")
        assert result == [
            "Mitochondria are membrane-bound organelles that generate most of the cell's ATP supply"
        ]

    def test_whitespace_only_slide_text(self):
        assert split_sentences("   \n\n  \n", source_format="pptx") == []

    def test_empty_string_pptx(self):
        assert split_sentences("", source_format="pptx") == []

    def test_question_fragment_bullet(self):
        text = "- Why do cells divide?"
        result = split_sentences(text, source_format="pptx")
        assert result == ["Why do cells divide?"]

    def test_default_source_format_is_still_pdf_behavior(self):
        text = "The mitochondria is the\npowerhouse of the cell."
        result = split_sentences(text, source_format="pdf")
        assert result == ["The mitochondria is the powerhouse of the cell."]

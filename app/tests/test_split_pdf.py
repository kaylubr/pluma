from app.services.split import split_sentences


class TestSplitSentencesPDF:
    def test_abbreviation_does_not_split(self):
        text = "Dr. Smith discovered polonium."
        result = split_sentences(text)
        assert result == ["Dr. Smith discovered polonium."]

    def test_decimal_number_does_not_split(self):
        text = "The value is 3.14 in this case."
        result = split_sentences(text)
        assert result == ["The value is 3.14 in this case."]    

    def test_multiple_sentences_on_one_line(self):
        text = "Cells divide. Mitosis has four phases."
        result = split_sentences(text)
        assert result == ["Cells divide.", "Mitosis has four phases."]

    def test_mid_sentence_line_wrap_rejoined(self):
        text = "The mitochondria is the\npowerhouse of the cell."
        result = split_sentences(text)
        assert result == ["The mitochondria is the powerhouse of the cell."]

    def test_terminal_punctuation_not_joined_to_next(self):
        text = "Cells divide.\nMitosis has four phases."
        result = split_sentences(text)
        assert result == ["Cells divide.", "Mitosis has four phases."]

    def test_empty_input_returns_empty_list(self):
        assert split_sentences("") == []
        assert split_sentences("   ") == []
        assert split_sentences("\n\n\n") == []

    def test_single_sentence_no_trailing_punctuation(self):
        text = "Final sentence"
        result = split_sentences(text)
        assert result == ["Final sentence"]

    def test_blank_lines_filtered_out(self):
        text = "First paragraph.\n\n\nSecond paragraph."
        result = split_sentences(text)
        assert result == ["First paragraph.", "Second paragraph."]

    def test_handles_initialisms(self):
        text = "The U.S. government funded the research."
        result = split_sentences(text)
        assert result == ["The U.S. government funded the research."]

    def test_handles_ellipsis(self):
        text = "Wait... what happened?"
        result = split_sentences(text)
        assert result == ["Wait... what happened?"]

    def test_mixed_wrapping_and_complete_sentences(self):
        text = "The mitochondria is the\npowerhouse of the cell.\n\nCells divide. Mitosis occurs."
        result = split_sentences(text)
        assert "The mitochondria is the powerhouse of the cell." in result
        assert "Cells divide." in result
        assert "Mitosis occurs." in result
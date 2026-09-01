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


class TestSplitPDFJoinHeuristic:
    # Verbatim post-clean lines from real_document.pdf, the confirmed smoke-test
    # failure: the slide title used to be glued onto the body sentence into one
    # merged card. Bullet glyphs are stripped by the Clean stage before this
    # text reaches Split.
    SMOKE_REPRO = (
        "Emotion Classification\n"
        "Emotion classification goes beyond polarity to identify\n"
        "specific emotions like joy, anger, sadness, fear, surprise, or\n"
        "disgust.\n"
        "This is useful for nuanced analysis, such as in mental\n"
        "health apps or brand sentiment tracking.\n"
        "It often relies on emotion lexicons (anger, fear, sadness,\n"
        "calm, strong, and happiness) and matching words to\n"
        "emotion categories.\n"
        "Multiple emotions can be detected in one text.\n"
        "Emotion Classification\n"
        "A basic approach:\n"
        "Use an emotion lexicon where words are mapped to emotions"
    )

    def test_smoke_repro_slide_title_not_merged_into_body_sentence(self):
        sentences = split_sentences(self.SMOKE_REPRO, source_format="pdf")
        assert any(s == "Emotion Classification" for s in sentences)
        assert not any("Classification" in s and "polarity" in s for s in sentences)
        assert any(
            s
            == "Emotion classification goes beyond polarity to identify "
            "specific emotions like joy, anger, sadness, fear, surprise, or disgust."
            for s in sentences
        )
        assert any(s == "A basic approach:" for s in sentences)

    def test_two_unpunctuated_capitalized_fragments_stay_separate(self):
        text = "Emotion Classification\nAspect-Based Sentiment Analysis"
        sentences = split_sentences(text, source_format="pdf")
        assert sentences == [
            "Emotion Classification",
            "Aspect-Based Sentiment Analysis",
        ]

    def test_trailing_comma_forces_join_into_uppercase_next_line(self):
        text = (
            "Mitochondria are membrane-bound organelles,\n"
            "Their main role is to produce ATP."
        )
        sentences = split_sentences(text, source_format="pdf")
        assert sentences == [
            "Mitochondria are membrane-bound organelles, Their main role is to produce ATP."
        ]

    def test_standalone_label_survives_as_own_entry(self):
        text = "Key organelles\nMitochondria produce ATP."
        sentences = split_sentences(text, source_format="pdf")
        assert sentences == ["Key organelles", "Mitochondria produce ATP."]

    def test_wrapped_sentence_breaking_before_proper_noun_stays_two_fragments(self):
        # Known, accepted limitation: a genuinely wrapped sentence that breaks
        # right before a capitalized proper noun is under-merged into two
        # fragments, because the continuation does not start lowercase. Solving
        # it properly needs layout data from the original PDF, which is a much
        # larger feature than this heuristic is scoped for.
        text = (
            "The discovery of\n"
            "Radium and polonium by Marie Curie changed chemistry."
        )
        sentences = split_sentences(text, source_format="pdf")
        assert sentences == [
            "The discovery of",
            "Radium and polonium by Marie Curie changed chemistry.",
        ]

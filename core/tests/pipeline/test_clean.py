from core.services.analyze import analyze_sentence
from core.services.clean import clean_markdown
from core.services.generate import generate_cloze
from core.services.split import split_sentences


class TestCleanMarkdown:
    def test_removes_headings(self):
        text = "# Lesson 1: Biology\nCells are the basic unit of life."
        result = clean_markdown(text)
        assert "# Lesson 1: Biology" not in result
        assert "Cells are the basic unit of life." in result

    def test_removes_atx_headings(self):
        text = "## Subheading\nContent here."
        result = clean_markdown(text)
        assert "## Subheading" not in result
        assert "Content here." in result

    def test_removes_bullet_points(self):
        text = "- First point\n- Second point\nNormal text."
        result = clean_markdown(text)
        assert "- First point" not in result
        assert "- Second point" not in result
        assert "Normal text." in result

    def test_removes_numbered_list(self):
        text = "1. First item\n2. Second item\nParagraph."
        result = clean_markdown(text)
        assert "1. First item" not in result
        assert "2. Second item" not in result
        assert "Paragraph." in result

    def test_removes_bold_markers(self):
        text = "**Bold text** and normal text."
        result = clean_markdown(text)
        assert "**" not in result
        assert "Bold text and normal text." in result

    def test_removes_italic_markers(self):
        text = "*Italic text* and normal text."
        result = clean_markdown(text)
        assert "*" not in result
        assert "Italic text and normal text." in result

    def test_removes_table_pipes(self):
        text = "| Header | Value |\n| --- | --- |\n| Cell | Data |\nParagraph."
        result = clean_markdown(text)
        assert "|" not in result
        assert "Paragraph." in result

    def test_preserves_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph."
        result = clean_markdown(text)
        assert "First paragraph." in result
        assert "Second paragraph." in result

    def test_skips_heading_lines_entirely(self):
        text = "# Heading to skip\nContent to keep.\n## Another heading\nMore content."
        result = clean_markdown(text)
        assert "Heading to skip" not in result
        assert "Another heading" not in result
        assert "Content to keep." in result
        assert "More content." in result

    def test_handles_empty_input(self):
        assert clean_markdown("") == ""
        assert clean_markdown("   ") == ""

    def test_handles_mixed_content(self):
        text = "# Title\n\n**Bold** and *italic* text.\n\n- Bullet 1\n- Bullet 2\n\nFinal sentence."
        result = clean_markdown(text)
        assert "Title" not in result
        assert "Bold" in result
        assert "italic" in result
        assert "Bullet 1" in result
        assert "Bullet 2" in result
        assert "Final sentence." in result
        assert "**" not in result
        assert "*" not in result
        assert "-" not in result.split("Final")[0]

    def test_drops_horizontal_rule(self):
        text = "Cells divide.\n---\nMitosis has four phases."
        result = clean_markdown(text)
        assert "---" not in result
        assert "Cells divide." in result
        assert "Mitosis has four phases." in result

    def test_drops_horizontal_rule_variants(self):
        text = "Line one.\n***\nLine two.\n___\nLine three."
        result = clean_markdown(text)
        assert "***" not in result
        assert "___" not in result
        assert "Line one." in result
        assert "Line two." in result
        assert "Line three." in result

    def test_drops_table_rows_entirely(self):
        text = "| Mitochondria | Powerhouse | ATP |\n| Cell | Nucleus | DNA |\nParagraph here."
        result = clean_markdown(text)
        assert "|" not in result
        assert "Mitochondria" not in result
        assert "Powerhouse" not in result
        assert "ATP" not in result
        assert "Cell" not in result
        assert "Nucleus" not in result
        assert "DNA" not in result
        assert "Paragraph here." in result

    def test_drops_table_separator_row(self):
        text = "| Header | Value |\n| --- | --- |\n| Cell | Data |\nKeep this."
        result = clean_markdown(text)
        assert "|" not in result
        assert "---" not in result
        assert "Keep this." in result

    def test_strips_links_keeps_text(self):
        text = "See [Krebs cycle](https://example.com) for details."
        result = clean_markdown(text)
        assert "https://example.com" not in result
        assert "[Krebs cycle]" not in result
        assert "Krebs cycle" in result

    def test_strips_images_keeps_alt_text(self):
        text = "Diagram: ![mitochondria](img.png) shows structure."
        result = clean_markdown(text)
        assert "img.png" not in result
        assert "![mitochondria]" not in result
        assert "mitochondria" in result

    def test_asterisk_multiplication_edge_case(self):
        text = "Calculate 5 * 3 = 15 and 2 * 4 = 8."
        result = clean_markdown(text)
        assert "5  3 = 15" in result

    def test_collapses_multiple_blank_lines(self):
        text = "Line one.\n\n\n\nLine two."
        result = clean_markdown(text)
        assert "Line one." in result
        assert "Line two." in result
        assert result.count("\n\n") <= 1


class TestCleanBulletGlyphs:
    def test_removes_unicode_bullet_at_line_start(self):
        text = "• Custom lexicons let you tailor analysis to your needs."
        result = clean_markdown(text)
        assert "•" not in result
        assert "Custom lexicons let you tailor analysis to your needs." in result

    def test_removes_bullets_from_realistic_extracted_text(self):
        text = (
            "VADER excels with social media (handling emojis and slang),\n"
            "• TextBlob is simple for general text\n"
            "• Custom lexicons let you tailor analysis to your needs."
        )
        result = clean_markdown(text)
        assert "•" not in result
        assert "TextBlob is simple for general text" in result
        assert "Custom lexicons let you tailor analysis to your needs." in result

    def test_removes_embedded_bullet_within_a_line(self):
        text = "general text • Custom lexicons let you tailor analysis"
        result = clean_markdown(text)
        assert "•" not in result
        assert "Custom lexicons let you tailor analysis" in result

    def test_removes_common_bullet_glyph_variants(self):
        for glyph in ["•", "◦", "‣", "▪", "▫", "⁃"]:
            result = clean_markdown(f"{glyph} Example sentence.")
            assert glyph not in result
            assert "Example sentence." in result


class TestBulletRegressionPipeline:
    def test_bullet_glyph_never_reaches_downstream_or_becomes_an_answer(self):
        text = (
            "VADER excels with social media (handling emojis and slang),\n"
            "• TextBlob is simple for general text\n"
            "• Custom lexicons let you tailor analysis to your needs."
        )
        cleaned = clean_markdown(text)
        sentences = split_sentences(cleaned, "pdf")
        assert sentences
        assert all("•" not in sentence for sentence in sentences)
        for sentence in sentences:
            cloze = generate_cloze(analyze_sentence(sentence))
            if cloze is not None:
                assert "•" not in cloze.answer
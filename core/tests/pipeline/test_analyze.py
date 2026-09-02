from core.services.analyze import AnalyzedSentence, Candidate, analyze_sentence
from core.tests.helper import make_analyzed


class TestAnalyzeNounPhrases:
    def test_extracts_full_multi_word_phrase(self):
        result = analyze_sentence("Lexicon-based methods analyze sentiment.")
        assert "Lexicon-based methods" in result.noun_phrases

    def test_strips_leading_determiner_from_phrase(self):
        result = analyze_sentence("The mitochondria produce energy.")
        assert "mitochondria" in result.noun_phrases

    def test_no_meaningful_phrase_keeps_single_nouns(self):
        result = analyze_sentence("Ribosomes synthesize proteins.")
        assert any(n.lower() == "proteins" for n in result.nouns)

    def test_empty_input_returns_empty_phrases(self):
        result = analyze_sentence("")
        assert isinstance(result, AnalyzedSentence)
        assert result.noun_phrases == []

        result2 = analyze_sentence("   ")
        assert result2.noun_phrases == []


class TestAnalyzeCandidates:
    def test_entity_candidate_with_label(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        marie = next(c for c in result.candidates if c.text == "Marie Curie")
        assert marie.kind == "entity"
        assert marie.entity_label == "PERSON"
        assert marie.rejected is None

    def test_numeric_entity_candidate_rejected(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        year = next(c for c in result.candidates if c.text == "1898")
        assert year.kind == "entity"
        assert year.entity_label == "DATE"
        assert year.rejected == "numeric"

    def test_noun_candidate_for_single_token(self):
        result = analyze_sentence("Ribosomes synthesize proteins.")
        proteins = next(c for c in result.candidates if c.text == "proteins")
        assert proteins.kind == "noun"
        assert proteins.rejected is None

    def test_phrase_candidate_for_multiword_concept(self):
        result = analyze_sentence("Lexicon-based methods analyze sentiment.")
        phrase = next(c for c in result.candidates if c.text == "Lexicon-based methods")
        assert phrase.kind == "phrase"
        assert phrase.rejected is None

    def test_identifier_phrase_and_contained_noun_flagged(self):
        result = analyze_sentence("Process A holds R and wants S")
        phrase = next(c for c in result.candidates if c.text == "Process A")
        assert phrase.identifier_like is True
        process = next(c for c in result.candidates if c.text == "Process")
        assert process.identifier_like is True

    def test_single_letter_nouns_rejected(self):
        result = analyze_sentence("Process A holds R and wants S")
        letters = {c.text for c in result.candidates if c.kind == "noun" and len(c.text) == 1}
        assert {"A", "R", "S"} <= letters
        assert all(
            c.rejected == "single_letter"
            for c in result.candidates
            if c.kind == "noun" and len(c.text) == 1
        )

    def test_hyphen_bridge_entity_rejected(self):
        result = make_analyzed(
            "One-shot Algorithm - Given a request from process P.",
            entities=[("Algorithm - Given", "ORG")],
            nouns=["Algorithm", "request", "process"],
        )
        span = next(c for c in result.candidates if c.text == "Algorithm - Given")
        assert span.rejected == "hyphen_bridge"

    def test_candidates_default_empty_for_empty_text(self):
        assert analyze_sentence("").candidates == []
        assert analyze_sentence("   ").candidates == []


class TestAnalyzeSentence:
    def test_named_entity_extraction(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        assert ("Marie Curie", "PERSON") in result.entities
        assert ("1898", "DATE") in result.entities

    def test_multi_word_entity_is_single_entry(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        entity_texts = [text for text, _ in result.entities]
        assert "Marie Curie" in entity_texts
        assert "Marie" not in entity_texts
        assert "Curie" not in entity_texts

    def test_noun_fallback_for_non_named_terms(self):
        result = analyze_sentence("Mitochondria produce energy for the cell.")
        assert any(n.lower() == "mitochondria" for n in result.nouns)

    def test_root_verb_detection(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        assert result.root_verb == "discovered"

    def test_root_verb_falls_back_when_root_token_is_not_a_verb(self):
        result = analyze_sentence("Ribosomes synthesize proteins")
        assert result.root_verb == "synthesize"

    def test_subject_falls_back_when_subject_relation_is_missed(self):
        result = analyze_sentence("Ribosomes synthesize proteins")
        assert result.subject_text == "Ribosomes"
        assert result.subject_is_pronoun is False

    def test_subject_detection_named_subject(self):
        result = analyze_sentence("Marie Curie discovered polonium in 1898.")
        assert result.subject_text == "Marie Curie"
        assert result.subject_is_pronoun is False

    def test_subject_detection_pronoun_subject(self):
        result = analyze_sentence("It was discovered in 1898.")
        assert result.subject_is_pronoun is True
        assert result.subject_text == "It"

    def test_empty_input_returns_sensible_defaults(self):
        result = analyze_sentence("")
        assert isinstance(result, AnalyzedSentence)
        assert result.text == ""
        assert result.entities == []
        assert result.nouns == []
        assert result.root_verb is None
        assert result.subject_text is None
        assert result.subject_is_pronoun is False

        result2 = analyze_sentence("   ")
        assert result2.entities == []
        assert result2.nouns == []
        assert result2.root_verb is None
        assert result2.subject_text is None
        assert result2.subject_is_pronoun is False

    def test_multiple_named_entities_membership(self):
        result = analyze_sentence("Albert Einstein was born in Ulm in 1879.")
        assert ("Albert Einstein", "PERSON") in result.entities
        assert ("Ulm", "GPE") in result.entities
        assert ("1879", "DATE") in result.entities

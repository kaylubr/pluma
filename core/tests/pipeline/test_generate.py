from core.services.generate import generate_cloze, generate_clozes, generate_candidate_clozes
from core.tests.helper import make_analyzed
from core.tests.regressions.regression_clozes import REGRESSION_CLOZES


class TestGenerateClozeEntity:
    def test_blanks_first_entity_not_subject_aware(self):
        result = generate_cloze(
            make_analyzed(
                "Mitochondria produce ATP.",
                entities=[("Mitochondria", "PERSON")],
                nouns=["Mitochondria", "ATP"],
            )
        )
        assert result is not None
        assert result.sentence == "Mitochondria produce ATP."
        assert result.text == "_____ produce ATP."
        assert result.answer == "Mitochondria"
        assert result.reason == "entity"

    def test_blanks_whole_entity_over_component_nouns(self):
        result = generate_cloze(
            make_analyzed(
                "Marie Curie discovered polonium in 1898.",
                entities=[("Marie Curie", "PERSON"), ("1898", "DATE")],
                nouns=["Marie", "Curie", "polonium"],
            )
        )
        assert result is not None
        assert result.text == "_____ discovered polonium in 1898."
        assert result.answer == "Marie Curie"
        assert result.reason == "entity"

    def test_numeric_entity_never_becomes_candidate(self):
        result = generate_cloze(
            make_analyzed(
                "Cells were discovered in 1665.",
                entities=[("1665", "DATE")],
                nouns=["Cells"],
            )
        )
        assert result is not None
        assert result.text == "_____ were discovered in 1665."
        assert result.answer == "Cells"
        assert result.reason == "noun"


class TestGenerateClozeEntitySanity:
    def test_formula_span_prefers_concept_phrase_over_noise_tokens(self):
        result = generate_cloze(
            make_analyzed(
                "The max score is computed as max = -1 at the end.",
                entities=[("max", "PERSON"), ("max = -1", "PERSON")],
                nouns=["max", "score", "max", "=", "end"],
                noun_phrases=["max score", "max", "=", "end"],
            )
        )
        assert result is not None
        assert result.answer == "max score"
        assert result.reason == "phrase"

    def test_rejects_entity_span_with_standalone_hyphen(self):
        result = generate_cloze(
            make_analyzed(
                "One-shot Algorithm - Given a request from process P.",
                entities=[("Algorithm - Given", "ORG")],
                nouns=["Algorithm", "request", "process"],
            )
        )
        assert result is not None
        assert result.answer != "Algorithm - Given"
        assert result.reason == "noun"

    def test_keeps_hyphenated_compound_entity_without_surrounding_spaces(self):
        result = generate_cloze(
            make_analyzed(
                "Jean-Paul Sartre wrote Being and Nothingness.",
                entities=[("Jean-Paul Sartre", "PERSON")],
                nouns=["Nothingness"],
            )
        )
        assert result is not None
        assert result.answer == "Jean-Paul Sartre"
        assert result.reason == "entity"

    def test_rejects_overly_long_entity_span_without_hyphen(self):
        result = generate_cloze(
            make_analyzed(
                "The Annual General Meeting Committee For Resource Allocation convened today.",
                entities=[
                    (
                        "The Annual General Meeting Committee For Resource Allocation",
                        "ORG",
                    )
                ],
                nouns=["committee", "today"],
            )
        )
        assert result is not None
        assert result.reason != "entity"

    def test_all_entities_incoherent_and_no_nouns_returns_none(self):
        result = generate_cloze(
            make_analyzed(
                "Hierarchical Algorithm - Given a request from process P.",
                entities=[("Hierarchical Algorithm - Given", "ORG")],
                nouns=[],
            )
        )
        assert result is None

    def test_falls_through_to_second_entity_when_first_is_incoherent(self):
        result = generate_cloze(
            make_analyzed(
                "Waiting for the Banker Algorithm to run, the Scheduling Algorithm - Given priority decides next.",
                entities=[
                    ("Scheduling Algorithm - Given", "ORG"),
                    ("Banker Algorithm", "LAW"),
                ],
                nouns=["priority"],
            )
        )
        assert result is not None
        assert result.answer == "Banker Algorithm"
        assert result.reason == "entity"


class TestGenerateClozeNoun:
    def test_blanks_first_noun_when_no_entity(self):
        result = generate_cloze(
            make_analyzed("Ribosomes synthesize proteins.", nouns=["proteins"])
        )
        assert result is not None
        assert result.text == "Ribosomes synthesize _____."
        assert result.answer == "proteins"
        assert result.reason == "noun"

    def test_blanks_first_noun_not_longest(self):
        result = generate_cloze(
            make_analyzed(
                "DNA carries genetic information.",
                nouns=["DNA", "information"],
            )
        )
        assert result is not None
        assert result.text == "_____ carries genetic information."
        assert result.answer == "DNA"
        assert result.reason == "noun"

    def test_blanks_subject_noun(self):
        result = generate_cloze(
            make_analyzed(
                "Cells are the basic unit of life.",
                nouns=["Cells", "unit", "life"],
            )
        )
        assert result is not None
        assert result.text == "_____ are the basic unit of life."
        assert result.answer == "Cells"
        assert result.reason == "noun"

    def test_blanks_passive_subject(self):
        result = generate_cloze(
            make_analyzed(
                "ATP is produced by mitochondria",
                nouns=["ATP", "mitochondria"],
            )
        )
        assert result is not None
        assert result.text == "ATP is produced by _____"
        assert result.answer == "mitochondria"
        assert result.reason == "noun"

    def test_blanks_mid_sentence_noun(self):
        result = generate_cloze(
            make_analyzed(
                "Both organelles have their own DNA",
                nouns=["organelles", "DNA"],
            )
        )
        assert result is not None
        assert result.text == "Both _____ have their own DNA"
        assert result.answer == "organelles"
        assert result.reason == "noun"

    def test_skips_duplicate_candidate_and_falls_through(self):
        result = generate_cloze(
            make_analyzed(
                "ATP and DNA produce ATP.",
                nouns=["ATP", "DNA", "ATP"],
            )
        )
        assert result is not None
        assert result.text == "ATP and _____ produce ATP."
        assert result.answer == "DNA"
        assert result.reason == "noun"


class TestGenerateClozePhraseTier:
    def test_prefers_phrase_over_component_nouns(self):
        result = generate_cloze(
            make_analyzed(
                "Lexicon-based methods analyze sentiment in product reviews.",
                nouns=["methods", "sentiment", "product", "reviews"],
                noun_phrases=["Lexicon-based methods"],
            )
        )
        assert result is not None
        assert result.answer == "Lexicon-based methods"
        assert result.reason == "phrase"
        assert result.text == "_____ analyze sentiment in product reviews."

    def test_no_phrases_behavior_unchanged(self):
        result = generate_cloze(
            make_analyzed("Ribosomes synthesize proteins.", nouns=["proteins"])
        )
        assert result is not None
        assert result.answer == "proteins"
        assert result.reason == "noun"

    def test_entity_still_precedes_phrase(self):
        result = generate_cloze(
            make_analyzed(
                "Marie Curie studied radiation in the lab.",
                entities=[("Marie Curie", "PERSON")],
                nouns=["radiation", "lab"],
                noun_phrases=["the lab"],
            )
        )
        assert result is not None
        assert result.answer == "Marie Curie"
        assert result.reason == "entity"

    def test_duplicate_phrase_skipped_and_falls_through(self):
        result = generate_cloze(
            make_analyzed(
                "Waiting for the resource allocator, the resource allocator grants access.",
                nouns=["resource", "allocator", "access"],
                noun_phrases=["resource allocator"],
            )
        )
        assert result is not None
        assert result.answer == "access"
        assert result.reason == "noun"


class TestGenerateClozeRarityPreference:
    def test_prefers_specific_noun_over_common(self):
        result = generate_cloze(
            make_analyzed("A process waits on a mutex.", nouns=["process", "mutex"])
        )
        assert result is not None
        assert result.answer == "mutex"
        assert result.reason == "noun"

    def test_reverse_supply_order_still_prefers_specific(self):
        result = generate_cloze(
            make_analyzed("A process waits on a mutex.", nouns=["mutex", "process"])
        )
        assert result is not None
        assert result.answer == "mutex"
        assert result.reason == "noun"

    def test_common_word_only_still_selected(self):
        result = generate_cloze(make_analyzed("A process runs.", nouns=["process"]))
        assert result is not None
        assert result.answer == "process"
        assert result.reason == "noun"

    def test_phrase_with_rarer_key_word_preferred(self):
        result = generate_cloze(
            make_analyzed(
                "Deadlock avoidance and process scheduling are two approaches.",
                nouns=[],
                noun_phrases=["Deadlock avoidance", "process scheduling"],
            )
        )
        assert result is not None
        assert result.answer == "Deadlock avoidance"
        assert result.reason == "phrase"

    def test_unscored_word_preferred_as_rare(self):
        result = generate_cloze(
            make_analyzed(
                "The process consumes the synaptosome.",
                nouns=["process", "synaptosome"],
            )
        )
        assert result is not None
        assert result.answer == "synaptosome"
        assert result.reason == "noun"

    def test_entity_precedence_unaffected(self):
        result = generate_cloze(
            make_analyzed(
                "Marie Curie studied polonium.",
                entities=[("Marie Curie", "PERSON")],
                nouns=["polonium"],
            )
        )
        assert result is not None
        assert result.answer == "Marie Curie"
        assert result.reason == "entity"


class TestGenerateClozeIdentifierDemotion:
    def test_identifier_only_sentence_returns_none(self):
        result = generate_cloze(
            make_analyzed(
                "Process A holds R and wants S",
                nouns=["Process", "A", "R", "S"],
                noun_phrases=["Process A"],
            )
        )
        assert result is None

    def test_named_entity_not_treated_as_identifier(self):
        result = generate_cloze(
            make_analyzed(
                "Marie Curie studied polonium.",
                entities=[("Marie Curie", "PERSON")],
                nouns=["polonium"],
            )
        )
        assert result is not None
        assert result.answer == "Marie Curie"
        assert result.reason == "entity"

    def test_concept_phrase_beats_identifier_phrase(self):
        result = generate_cloze(
            make_analyzed(
                "Waiting for process P, the scheduling algorithm decides next.",
                nouns=["process", "scheduling", "algorithm"],
                noun_phrases=["process P", "scheduling algorithm"],
            )
        )
        assert result is not None
        assert result.answer == "scheduling algorithm"
        assert result.reason == "phrase"


class TestGenerateCandidateClozes:
    def test_pool_ranks_entity_first(self):
        pool = generate_candidate_clozes(
            make_analyzed(
                "Marie Curie studied polonium in the lab.",
                entities=[("Marie Curie", "PERSON")],
                nouns=["polonium", "lab"],
                noun_phrases=["the lab"],
            )
        )
        assert pool
        assert pool[0].answer == "Marie Curie"
        assert pool[0].reason == "entity"

    def test_pool_orders_phrases_before_nouns(self):
        pool = generate_candidate_clozes(
            make_analyzed(
                "Waiting for the resource allocator, the scheduling algorithm grants access.",
                nouns=["resource", "allocator", "scheduling", "algorithm", "access"],
                noun_phrases=["scheduling algorithm", "resource allocator"],
            )
        )
        answers = [c.answer for c in pool]
        assert answers[0] in ("scheduling algorithm", "resource allocator")

    def test_pool_excludes_identifiers_and_duplicate_spans(self):
        pool = generate_candidate_clozes(
            make_analyzed(
                "Process P waits on the mutex.",
                nouns=["Process", "P", "mutex"],
                noun_phrases=["Process P"],
            )
        )
        assert pool
        assert all(c.answer != "Process P" for c in pool)
        assert pool[0].answer == "mutex"

    def test_pool_empty_for_no_eligible_candidate(self):
        assert generate_candidate_clozes(make_analyzed("Yes")) == []


class TestGenerateClozeNone:
    def test_all_candidates_duplicate_returns_none(self):
        result = generate_cloze(
            make_analyzed("DNA contains DNA.", nouns=["DNA", "DNA"])
        )
        assert result is None

    def test_no_candidates_returns_none(self):
        assert generate_cloze(make_analyzed("Yes")) is None

    def test_empty_text_returns_none(self):
        assert generate_cloze(make_analyzed("")) is None

    def test_whitespace_text_returns_none(self):
        assert generate_cloze(make_analyzed("   ")) is None


class TestGenerateClozeAnswerTraceability:
    def test_answer_is_word_boundary_match_in_sentence(self):
        for analyzed, _ in REGRESSION_CLOZES:
            result = generate_cloze(analyzed)
            if result is None:
                continue
            assert result.answer in analyzed.text


class TestGenerateClozes:
    def test_batch_matches_input_order_and_keeps_none(self):
        inputs = [
            make_analyzed("Ribosomes synthesize proteins.", nouns=["proteins"]),
            make_analyzed("Yes"),
            make_analyzed("Mitochondria produce ATP.", entities=[("Mitochondria", "PERSON")], nouns=["Mitochondria", "ATP"]),
        ]
        results = generate_clozes(inputs)
        assert len(results) == len(inputs)
        assert results[0].answer == "proteins"
        assert results[1] is None
        assert results[2].answer == "Mitochondria"

    def test_empty_list(self):
        assert generate_clozes([]) == []


class TestRegressionClozes:
    def test_regression_set_answers(self):
        for analyzed, expected_answer in REGRESSION_CLOZES:
            result = generate_cloze(analyzed)
            if expected_answer is None:
                assert result is None
                continue
            assert result is not None
            assert result.answer == expected_answer

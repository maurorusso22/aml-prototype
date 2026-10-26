"""The LLM enricher with a fake backend: correct plumbing, and fallback on every failure."""

import json
import math
from collections.abc import Callable

from pydantic import BaseModel

from aml_reporter.enrichment import LLMEnricher, enrichable
from aml_reporter.enrichment.base import normalise
from aml_reporter.enrichment.llm_enricher import BATCH_SIZE
from aml_reporter.enrichment.tasks import CounterpartyAnswers, IbanAnswers, PurposeAnswers
from aml_reporter.llm import LLMError, parse_json
from aml_reporter.models import EnrichmentSource
from aml_reporter.synthetic import GeneratedCase

type Corruption = Callable[[str, dict[str, object]], dict[str, object] | None]


class OracleClient:
    """Fake backend answering from the ground-truth labels, optionally corrupting answers."""

    def __init__(
        self, case: GeneratedCase, corrupt: Corruption | None = None, down: bool = False
    ) -> None:
        """Index the labels by description and by name.

        Args:
            case: Case whose labels hold the right answers.
            corrupt: Rewrites or drops (returns None) an answer, given the schema name.
            down: Fail every call, like an unreachable API.
        """
        texts = {tx.transaction_id: normalise(tx.description) for tx in case.bundle.transactions}
        labels = case.labels.transactions
        self.by_text = {texts[label.transaction_id]: label for label in labels}
        self.types = {label.counterparty_name: label.counterparty_type for label in labels}
        self.corrupt, self.down, self.calls = corrupt, down, 0

    def complete[T: BaseModel](self, system: str, user: str, schema: type[T]) -> T:
        """Answer every item correctly, then apply the corruption.

        Args:
            system: Task prompt, unused.
            user: Items as JSON text.
            schema: Answer schema, which tells the task.

        Returns:
            The parsed answer, exactly as a real backend would return it.
        """
        self.calls += 1
        if self.down:
            raise LLMError("backend unreachable")
        answers = [self._answer(schema.__name__, item) for item in json.loads(user)]
        if self.corrupt:
            corrupted = (self.corrupt(schema.__name__, answer) for answer in answers)
            answers = [answer for answer in corrupted if answer is not None]
        return parse_json(json.dumps({"answers": answers}), schema)

    def _answer(self, schema: str, item: dict[str, str]) -> dict[str, object]:
        """Look up the right answer for one item.

        Args:
            schema: Name of the answer schema.
            item: Item sent to the model.

        Returns:
            The answer as raw JSON data.
        """
        if schema == "TypeAnswers":
            return {"id": item["id"], "counterparty_type": self.types[item["name"]]}
        label = self.by_text[item["text"]]
        field, value = {
            IbanAnswers.__name__: ("iban", label.counterparty_iban),
            CounterpartyAnswers.__name__: ("counterparty_name", label.counterparty_name),
            PurposeAnswers.__name__: ("payment_purpose", label.payment_purpose),
        }[schema]
        return {"id": item["id"], field: value}


def test_correct_answers_reproduce_the_labels(pass_through_case: GeneratedCase) -> None:
    """With right answers, every enrichment comes from the LLM and equals its label."""
    enrichments = LLMEnricher(OracleClient(pass_through_case)).enrich(
        pass_through_case.bundle.transactions
    )
    labels = {label.transaction_id: label for label in pass_through_case.labels.transactions}
    assert len(enrichments) == len(labels)
    for enrichment in enrichments:
        label = labels[enrichment.transaction_id]
        assert enrichment.source is EnrichmentSource.LLM
        assert enrichment.counterparty_name == label.counterparty_name
        assert enrichment.counterparty_iban == label.counterparty_iban
        assert enrichment.counterparty_type == label.counterparty_type
        assert enrichment.payment_purpose == label.payment_purpose


def test_invented_values_fall_back_to_the_baseline(pass_through_case: GeneratedCase) -> None:
    """An IBAN or a name that is not in the text sends the record to the baseline."""

    def invent(schema: str, answer: dict[str, object]) -> dict[str, object]:
        """Replace every IBAN with one that appears in no description.

        Args:
            schema: Name of the answer schema.
            answer: Correct answer.

        Returns:
            The corrupted answer.
        """
        if schema == "IbanAnswers":
            return {**answer, "iban": "IT00X9999999999999999999999"}
        return answer

    transactions = pass_through_case.bundle.transactions
    enrichments = LLMEnricher(OracleClient(pass_through_case, invent)).enrich(transactions)
    assert {enrichment.source for enrichment in enrichments} == {EnrichmentSource.BASELINE}


def test_missing_answer_affects_only_its_item(pass_through_case: GeneratedCase) -> None:
    """When an answer is dropped, only the transactions with that description fall back."""

    def drop_first(schema: str, answer: dict[str, object]) -> dict[str, object] | None:
        """Drop the first purpose answer of every batch.

        Args:
            schema: Name of the answer schema.
            answer: Correct answer.

        Returns:
            None for the dropped answer, the answer otherwise.
        """
        return None if schema == "PurposeAnswers" and answer["id"] == 0 else answer

    transactions = enrichable(pass_through_case.bundle.transactions)
    dropped = set(sorted({normalise(tx.description) for tx in transactions})[::BATCH_SIZE])
    enrichments = LLMEnricher(OracleClient(pass_through_case, drop_first)).enrich(transactions)
    for tx, enrichment in zip(transactions, enrichments, strict=True):
        fell_back = normalise(tx.description) in dropped
        assert enrichment.source is (
            EnrichmentSource.BASELINE if fell_back else EnrichmentSource.LLM
        )


def test_backend_failure_never_crashes(pass_through_case: GeneratedCase) -> None:
    """An unreachable backend yields baseline enrichments for every transaction."""
    enricher = LLMEnricher(OracleClient(pass_through_case, down=True))
    enrichments = enricher.enrich(pass_through_case.bundle.transactions)
    assert len(enrichments) == len(pass_through_case.labels.transactions)
    assert {enrichment.source for enrichment in enrichments} == {EnrichmentSource.BASELINE}


def test_batches_and_cache(pass_through_case: GeneratedCase) -> None:
    """Calls are batched per task, and a second run is served entirely from the cache."""
    client = OracleClient(pass_through_case)
    enricher = LLMEnricher(client)
    transactions = enrichable(pass_through_case.bundle.transactions)
    enricher.enrich(transactions)
    texts = {normalise(tx.description) for tx in transactions}
    names = {label.counterparty_name for label in pass_through_case.labels.transactions}
    expected = 3 * math.ceil(len(texts) / BATCH_SIZE) + math.ceil(len(names) / BATCH_SIZE)
    assert client.calls == expected
    enricher.enrich(transactions)
    assert client.calls == expected

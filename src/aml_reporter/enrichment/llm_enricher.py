"""Enrichment through an LLM backend: batched calls, a cache, validation, and fallback."""

import json
import logging
from collections import Counter
from collections.abc import Sequence

from pydantic import ValidationError

from ..llm import LLMClient, LLMError
from ..models import Enrichment, EnrichmentSource, Transaction
from .base import enrichable, normalise
from .baseline import BaselineEnricher
from .tasks import COUNTERPARTY, COUNTERPARTY_TYPE, DESCRIPTION_TASKS, IBAN, PAYMENT_PURPOSE, Task
from .validation import InvalidAnswerError

BATCH_SIZE = 20  # Inputs per request: enough to save calls, few enough to keep answers aligned

logger = logging.getLogger(__name__)

type Key = tuple[str, str]


class LLMEnricher:
    """Asks an LLM every task, and falls back to the baseline for any transaction with a failure.

    Answers are cached by task and normalised input, so repeated descriptions cost one call.
    Inputs the model skips are asked once more, in a batch of their own. A transaction is
    enriched by the LLM only if every one of its answers passed validation; otherwise the
    whole record comes from the baseline, so `source` stays truthful.
    """

    def __init__(self, client: LLMClient, fallback: BaselineEnricher | None = None) -> None:
        """Create the enricher.

        Args:
            client: LLM backend.
            fallback: Enricher used when an answer is missing or invalid.
        """
        self.client = client
        self.rejections: Counter[str] = Counter()  # Failed answers, by task and reason
        self._fallback = fallback or BaselineEnricher()
        self._answers: dict[Key, object] = {}
        self._failed: set[Key] = set()

    def enrich(self, transactions: Sequence[Transaction]) -> list[Enrichment]:
        """Enrich every wire transfer and direct debit.

        Args:
            transactions: Any transactions; card and cash operations are skipped.

        Returns:
            One enrichment per enrichable transaction, in input order.
        """
        targets = enrichable(transactions)
        texts = sorted({normalise(tx.description) for tx in targets})
        for task in DESCRIPTION_TASKS:
            self._run(task, texts)
        names = {self._answers.get((COUNTERPARTY.name, text)) for text in texts}
        self._run(COUNTERPARTY_TYPE, sorted(name for name in names if isinstance(name, str)))
        enrichments = [self._enrichment(tx) for tx in targets]
        sources = Counter(enrichment.source for enrichment in enrichments)
        logger.info("enriched %d transactions: %s", len(enrichments), dict(sources))
        return enrichments

    def _run(self, task: Task, inputs: Sequence[str]) -> None:
        """Answer every input not answered yet, in batches.

        Args:
            task: Task to run.
            inputs: Descriptions or names.
        """
        done = self._answers.keys() | self._failed
        pending = [value for value in inputs if (task.name, value) not in done]
        unanswered: list[str] = []
        for start in range(0, len(pending), BATCH_SIZE):
            unanswered += self._run_batch(task, pending[start : start + BATCH_SIZE])
        if unanswered:
            logger.info("%s: asking again for %d unanswered inputs", task.name, len(unanswered))
        for start in range(0, len(unanswered), BATCH_SIZE):
            still = self._run_batch(task, unanswered[start : start + BATCH_SIZE])
            if still:
                self._failed.update((task.name, value) for value in still)
                self.rejections[f"{task.name}: no answer after retry"] += len(still)

    def _run_batch(self, task: Task, batch: Sequence[str]) -> list[str]:
        """Ask one batch, store each answer that passes its check, and report the gaps.

        Args:
            task: Task to run.
            batch: Inputs; their position is the item id sent to the model.

        Returns:
            Inputs the model skipped or answered twice, left for the caller to retry.
        """
        items = [{"id": number, task.input_key: value} for number, value in enumerate(batch)]
        try:
            result = self.client.complete(task.prompt, json.dumps(items), task.schema)
        except LLMError as error:
            logger.warning("%s: batch of %d failed: %s", task.name, len(batch), error)
            self._failed.update((task.name, value) for value in batch)
            self.rejections[f"{task.name}: batch failed"] += len(batch)
            return []
        counts = Counter(answer.id for answer in result.answers)
        by_id = {answer.id: answer for answer in result.answers if counts[answer.id] == 1}
        unanswered = [value for number, value in enumerate(batch) if number not in by_id]
        for number, value in enumerate(batch):
            if number not in by_id:
                continue
            try:
                self._answers[(task.name, value)] = task.check(
                    getattr(by_id[number], task.field), value
                )
            except InvalidAnswerError as error:
                logger.info("%s: answer %d rejected: %s", task.name, number, error)
                self._failed.add((task.name, value))
                self.rejections[f"{task.name}: {error}"] += 1
        return unanswered

    def _enrichment(self, transaction: Transaction) -> Enrichment:
        """Assemble one enrichment from validated answers, or fall back to the baseline.

        Args:
            transaction: A wire transfer or direct debit.

        Returns:
            The enrichment, with source `llm` or `baseline`.
        """
        text = normalise(transaction.description)
        keys = [(task.name, text) for task in DESCRIPTION_TASKS]
        name = self._answers.get((COUNTERPARTY.name, text))
        if isinstance(name, str):
            keys.append((COUNTERPARTY_TYPE.name, name))
        if any(key not in self._answers for key in keys):
            return self._fallback.enrich_one(transaction)
        try:
            return Enrichment.model_validate(
                {
                    "transaction_id": transaction.transaction_id,
                    "counterparty_name": name,
                    "counterparty_iban": self._answers[(IBAN.name, text)],
                    "counterparty_type": self._answers.get((COUNTERPARTY_TYPE.name, str(name))),
                    "payment_purpose": self._answers[(PAYMENT_PURPOSE.name, text)],
                    "source": EnrichmentSource.LLM,
                }
            )
        except ValidationError:
            return self._fallback.enrich_one(transaction)

"""Adapter that turns a general text LLM into a Text-to-SQL generator."""

from __future__ import annotations

from queryguard.llm.base import TextLLM
from queryguard.llm.prompts import SQL_SYSTEM_PROMPT, generation_prompt, repair_prompt
from queryguard.llm.utils import extract_sql


class LLMSQLGenerator:
    def __init__(self, client: TextLLM) -> None:
        self.client = client

    def generate_sql(self, question: str, schema_context: str) -> str:
        text = self.client.complete(
            generation_prompt(question, schema_context),
            system_prompt=SQL_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        return extract_sql(text)

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        previous_sql: str,
        error: str,
    ) -> str:
        text = self.client.complete(
            repair_prompt(question, schema_context, previous_sql, error),
            system_prompt=SQL_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        return extract_sql(text)

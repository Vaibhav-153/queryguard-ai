"""Convert relational schema objects into retrieval documents."""

from dataclasses import dataclass

from queryguard.database.schema import TableSchema


@dataclass(frozen=True, slots=True)
class SchemaDocument:
    table: str
    text: str


def build_schema_documents(schema: list[TableSchema]) -> list[SchemaDocument]:
    documents: list[SchemaDocument] = []
    for table in schema:
        column_names = ", ".join(column.name for column in table.columns)
        relationships = ", ".join(
            f"{fk.from_column} references {fk.target_table}.{fk.target_column}"
            for fk in table.foreign_keys
        )
        text = f"Table {table.name}. Columns: {column_names}."
        if relationships:
            text += f" Relationships: {relationships}."
        documents.append(SchemaDocument(table=table.name, text=text))
    return documents

from queryguard.llm.ollama import extract_sql


def test_extract_sql_from_markdown_fence():
    text = "```sql\nSELECT COUNT(*) FROM Customer;\n```"
    assert extract_sql(text) == "SELECT COUNT(*) FROM Customer"


def test_extract_sql_from_prefixed_text():
    text = "Here is the query: SELECT Name FROM Artist;"
    assert extract_sql(text) == "SELECT Name FROM Artist"

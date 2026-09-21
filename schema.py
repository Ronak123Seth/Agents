from typing import Any, Literal
from pydantic import BaseModel, ValidationError

class SQLAgentResult(BaseModel):
    status: Literal["success", "no_results", "out_of_scope"]
    sql_query: str
    columns: list[str]
    rows: list[dict[str, Any]]
    final_answer: str


def parse_sql_agent_response(response_text: str) -> dict[str, Any]:
    try:
        result = SQLAgentResult.model_validate_json(response_text)
    except ValidationError:
        return {
            "status": "out_of_scope",
            "final_answer": "I can only answer questions about the SQLite used-cars database.",
        }

    if result.status == "out_of_scope":
        return {
            "status": "out_of_scope",
            "final_answer": result.final_answer,
        }

    if result.status == "no_results" or not result.rows:
        return {
            "status": "no_results",
            "final_answer": result.final_answer or "Can you explain what you're looking for?",
        }

    return result.model_dump()
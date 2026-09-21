from database import execute_sql_query, get_database_schema

def calculate_total_salary(salaries):
    return sum(salaries)

def calculate_average_salary(salaries):
    if not salaries:
        return 0
    return sum(salaries) / len(salaries)

tools = [
    {
        "type": "function",
        "name": "get_database_schema",
        "description": "Return the available SQLite tables and their columns.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": get_database_schema,
    },
    {
        "type": "function",
        "name": "execute_sql_query",
        "description": "Execute one safe, read-only SQL query and return its rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A single SELECT or WITH query.",
                }
            },
            "required": ["sql"],
        },
        "handler": execute_sql_query,
    },
    {
        "type": "function",
        "name": "calculate_total_salary",
        "description": "Calculate the total salary from a list of salaries.",
        "parameters": {
            "type": "object",
        "properties": {
            "salaries": {
                "type": "array",
                "items": {"type": "number"}
            }
        },
        "required": ["salaries"]
    },
    "handler": calculate_total_salary,
},
    {
    "type": "function",
    "name": "calculate_average_salary",
    "description": "Calculate the average salary from a list of salaries.",
    "parameters": {
        "type": "object",
        "properties": {
            "salaries": {
                "type": "array",
                "items": {"type": "number"}
            }
        },
        "required": ["salaries"]
    },
    "handler": calculate_average_salary,
},
]
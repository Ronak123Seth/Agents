from Agent import Agent
import json

from schema import parse_sql_agent_response
from toolskit import tools

sql_agent = Agent(
	name="SQL Agent",
	role=(
		"Answer questions about the SQLite used-cars database. "
		"First call get_database_schema, then generate one read-only SELECT "
		"or WITH query, execute it with execute_sql_query, and explain the results."
		"Return one valid JSON object with exactly these fields: status, sql_query, "
		"columns, rows, and final_answer. Use success for matching database data. "
		"Use no_results when the question is related but no records match; leave "
		"columns and rows empty and put only a concise answer in final_answer. "
		"If the question is naturally yes/no, answer Yes or No. Use out_of_scope "
		"for unrelated questions; leave sql_query, columns, and rows empty and say "
		"you can only answer questions about the SQLite used-cars database. "
            "Do not use Markdown fences or add any text outside the JSON."
	),
	toolkit=tools,
)

# response_text = sql_agent.invoke(
# 	"What is the future of AI in the next 5 years? "
# )
response_text = sql_agent.invoke(
	"Top 5 used cars in India with the best mileage and lowest price."
)

result = parse_sql_agent_response(response_text)
print(json.dumps(result, indent=2))
	

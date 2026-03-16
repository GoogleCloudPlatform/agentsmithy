from pydantic import BaseModel

class AgentConfig(BaseModel):
    should_expand_intermediate_results: bool = False
    sql_query_key: str = "sql_query"
    query_validation_key: str = "query_validation"
    sql_query_results_key: str = "sql_query_results"
    answer_key: str = "final_answer"

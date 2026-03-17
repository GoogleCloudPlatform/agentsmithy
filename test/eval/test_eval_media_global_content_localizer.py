from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest


@pytest.mark.asyncio
async def eval():
    """Test the agent's basic ability via a session file."""
    await AgentEvaluator.evaluate(
        agent_module="agent_bar_v2",
        eval_dataset_file_path_or_dir="test/eval/evalsets/eval_media_global_content_localizer.json",
        
    )

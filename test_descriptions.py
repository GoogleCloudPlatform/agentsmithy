from agent_bar_v2.subagents.agent_registry import get_agent_descriptions_json

def test_desciptions():
    # Sample agent IDs to fetch descriptions for
    sample_agent_ids = [
        "medical_search_agent",
        "cyber_incident_response",
        "storage_access",
        "invalid_agent_id", # Should gracefully skip since it's not in the registry
    ]

    print(f"Testing with Agent IDs: {sample_agent_ids}\n")
    
    # Call the helper function
    output_json = get_agent_descriptions_json(sample_agent_ids)
    
    # Print out the formatted JSON response
    print("Output JSON:")
    print(output_json)

if __name__ == "__main__":
    test_desciptions()

def grade_output(expected_output, actual_output, grader_type):
    if grader_type == "exact_match":
        return 1.0 if expected_output == actual_output else 0.0
    elif grader_type == "partial_match":
        return len(set(expected_output.split()) & set(actual_output.split())) / len(set(expected_output.split()))
    elif grader_type == "LLM_match":
        # Placeholder: Use another LLM to assess similarity
        return 0.8  # Example score
    return 0.0
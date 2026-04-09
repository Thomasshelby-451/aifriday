import re
import json

# -------------------------------
# Input Guardrail
# -------------------------------
def input_guardrail(user_input: str) -> str:
    """
    Sanitize user input before sending to the LLM.
    - Mask IP addresses
    - Mask hostnames
    """
    # Mask IPv4 addresses
    user_input = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]', user_input)
    # Mask hostnames (simple pattern: words + dot + TLD)
    user_input = re.sub(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '[REDACTED_HOST]', user_input)
    return user_input


# -------------------------------
# Output Guardrail
# -------------------------------
def output_guardrail(model_output: str) -> str:
    """
    Validate and sanitize model output before returning to user.
    - Ensure JSON format
    - Mask IP addresses and hostnames
    """
    # Try to enforce JSON structure
    try:
        parsed = json.loads(model_output)
        safe_output = json.dumps(parsed, indent=2)
    except Exception:
        # If not valid JSON, wrap in safe fallback
        safe_output = json.dumps({"response": model_output})

    # Mask PII in the output
    safe_output = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]', safe_output)
    safe_output = re.sub(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '[REDACTED_HOST]', safe_output)

    return safe_output


# -------------------------------
# Example Usage
# -------------------------------
user_query = "Please list servers: 192.168.1.10 and test.example.com"
print("Raw Input:", user_query)

# Apply input guardrail
sanitized_input = input_guardrail(user_query)
print("Sanitized Input:", sanitized_input)

# Simulate model output
model_response = '{"servers": ["192.168.1.10", "test.example.com"]}'
print("Raw Output:", model_response)

# Apply output guardrail
safe_response = output_guardrail(model_response)
print("Safe Output:", safe_response)
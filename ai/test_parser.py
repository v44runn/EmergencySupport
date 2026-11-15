
from ai.gemini_parser import parse_request

messages = [
    "We need 100 blankets at the community center in San Jose.",
    "URGENT! Send 25 first aid kits to Santa Clara before 9 PM.",
    "Please deliver food to the shelter in Campbell.",
    "We need 60 bottles of water at the school in Milpitas."
]

for i, message in enumerate(messages, start=1):
    print(f"\n--- Test {i} ---")
    print("Input:", message)

    try:
        result = parse_request(message)
        print("Output:", result)
    except Exception as e:
        print("Error:", e)

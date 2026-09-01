from backend.app.agents.intent import extract_intent


message1 = (
    "I have chicken, spinach and rice. "
    "Give me a high-protein dinner under 30 minutes."
)

message2 = (
    "I have chicken breast, rice, spinach, Greek yogurt and onions. "
    "Dinner for 2, high protein, under 500 calories per serving, "
    "ready in 30 minutes. No peanuts. I prefer something spicy "
    "and Indian-inspired. I only have a stovetop and microwave."
)

result = extract_intent(message2)

print(result.model_dump_json(indent=2))
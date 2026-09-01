from backend.app.config.settings import get_settings
from backend.app.services.llm import client


settings = get_settings()


response = client.responses.create(
    model=settings.openai_model,
    input="Reply with exactly: MealMuse connection successful!",
)


print(response.output_text)
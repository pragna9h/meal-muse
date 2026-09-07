from sqlalchemy import text
import time
from openai import RateLimitError
from backend.app.config.settings import get_settings
from backend.app.database.connection import engine
from backend.app.services.llm import client


BATCH_SIZE = 100
MAX_RETRIES = 5
INITIAL_RETRY_DELAY_SECONDS = 2

def vector_to_string(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"


def generate_embeddings() -> None:
    settings = get_settings()

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT recipe_id, search_text
                FROM recipes
                WHERE embedding IS NULL
                ORDER BY recipe_id
                """
            )
        ).mappings().all()

    print(f"Recipes needing embeddings: {len(rows):,}")

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]

        delay = INITIAL_RETRY_DELAY_SECONDS

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.embeddings.create(
                    model=settings.openai_embedding_model,
                    input=[row["search_text"] for row in batch],
                )
                break

            except RateLimitError:
                if attempt == MAX_RETRIES:
                    raise

                print(
                    f"Rate limit reached. "
                    f"Retrying in {delay} seconds "
                    f"(attempt {attempt}/{MAX_RETRIES})..."
                )

                time.sleep(delay)
                delay *= 2                                                                     

        updates = [
            {
                "recipe_id": row["recipe_id"],
                "embedding": vector_to_string(result.embedding),
            }
            for row, result in zip(batch, response.data)
        ]

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE recipes
                    SET embedding = CAST(:embedding AS vector)
                    WHERE recipe_id = :recipe_id
                    """
                ),
                updates,
            )

        completed = min(start + BATCH_SIZE, len(rows))
        print(f"Embedded {completed:,}/{len(rows):,} recipes")


if __name__ == "__main__":
    generate_embeddings()
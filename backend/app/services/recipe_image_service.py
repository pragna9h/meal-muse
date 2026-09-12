# import json
# import re
# from typing import Any, Optional

# import httpx
# from sqlalchemy import text

# from backend.app.database.connection import engine


# REQUEST_TIMEOUT_SECONDS = 10.0

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/120.0 Safari/537.36"
#     )
# }


# def _find_recipe_object(data: Any) -> Optional[dict]:
#     if isinstance(data, dict):
#         recipe_type = data.get("@type")

#         if recipe_type == "Recipe":
#             return data

#         if isinstance(recipe_type, list) and "Recipe" in recipe_type:
#             return data

#         if "@graph" in data:
#             result = _find_recipe_object(data["@graph"])
#             if result:
#                 return result

#         for value in data.values():
#             result = _find_recipe_object(value)
#             if result:
#                 return result

#     elif isinstance(data, list):
#         for item in data:
#             result = _find_recipe_object(item)
#             if result:
#                 return result

#     return None


# def _extract_image_url(recipe_data: dict) -> Optional[str]:
#     image = recipe_data.get("image")

#     if isinstance(image, str):
#         return image

#     if isinstance(image, dict):
#         image_url = image.get("url")

#         if isinstance(image_url, str):
#             return image_url

#     if isinstance(image, list):
#         for item in image:
#             if isinstance(item, str):
#                 return item

#             if isinstance(item, dict):
#                 image_url = item.get("url")

#                 if isinstance(image_url, str):
#                     return image_url

#     return None


# def extract_recipe_image_url(source_url: str) -> Optional[str]:
#     try:
#         response = httpx.get(
#             source_url,
#             headers=HEADERS,
#             timeout=REQUEST_TIMEOUT_SECONDS,
#             follow_redirects=True,
#         )
#         response.raise_for_status()
#     except httpx.HTTPError:
#         return None

#     scripts = re.findall(
#         r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
#         response.text,
#         flags=re.IGNORECASE | re.DOTALL,
#     )

#     for script_content in scripts:
#         try:
#             data = json.loads(script_content.strip())
#         except json.JSONDecodeError:
#             continue

#         recipe_data = _find_recipe_object(data)

#         if not recipe_data:
#             continue

#         image_url = _extract_image_url(recipe_data)

#         if image_url:
#             return image_url

#     return None


# def save_recipe_image_url(recipe_id: str, image_url: str) -> None:
#     sql = text(
#         """
#         UPDATE recipes
#         SET image_url = :image_url
#         WHERE recipe_id = :recipe_id
#         """
#     )

#     with engine.begin() as connection:
#         connection.execute(
#             sql,
#             {
#                 "recipe_id": recipe_id,
#                 "image_url": image_url,
#             },
#         )


# def get_or_fetch_recipe_image(
#     recipe_id: str,
#     source_url: Optional[str],
#     existing_image_url: Optional[str],
# ) -> Optional[str]:
#     if existing_image_url:
#         return existing_image_url

#     if not source_url:
#         return None

#     image_url = extract_recipe_image_url(source_url)

#     if not image_url:
#         return None

#     save_recipe_image_url(recipe_id, image_url)

#     return image_url
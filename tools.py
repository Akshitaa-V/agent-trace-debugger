import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def calculator_tool(expression: str) -> dict:
    """
    Simple calculator tool.
    For safety, only numbers and arithmetic operators are allowed.
    """
    try:
        allowed_pattern = r"^[0-9+\-*/().\s]+$"

        if not re.match(allowed_pattern, expression):
            return {
                "status": "error",
                "output": None,
                "error": "Invalid mathematical expression"
            }

        result = eval(expression, {"__builtins__": {}})

        return {
            "status": "success",
            "output": result,
            "error": None
        }

    except Exception as e:
        return {
            "status": "error",
            "output": None,
            "error": str(e)
        }


def document_retrieval_tool(query: str) -> dict:
    """
    Simple keyword-based document retrieval tool.
    Searches the local documents.json file.
    Ignores common words and focuses on meaningful keywords.
    """
    try:
        file_path = BASE_DIR / "data" / "documents.json"

        with open(file_path, "r", encoding="utf-8") as file:
            documents = json.load(file)

        stop_words = {
            "what", "does", "the", "document", "say", "about",
            "is", "are", "a", "an", "of", "in", "to", "and"
        }

        query_words = [
            word.strip("?.!,").lower()
            for word in query.split()
            if word.strip("?.!,").lower() not in stop_words
        ]

        best_doc = None
        best_score = 0

        for doc in documents:
            content = doc["content"].lower()
            title = doc["title"].lower()

            score = 0
            for word in query_words:
                if word in title:
                    score += 3
                if word in content:
                    score += 1

            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc is None:
            return {
                "status": "error",
                "output": None,
                "error": "No relevant document found"
            }

        return {
            "status": "success",
            "output": best_doc,
            "error": None
        }

    except Exception as e:
        return {
            "status": "error",
            "output": None,
            "error": str(e)
        }


def structured_search_tool(category: str, city: str, max_price: int) -> dict:
    """
    Mock structured search tool.
    Searches search_data.json using category, city, and price.
    """
    try:
        file_path = BASE_DIR / "data" / "search_data.json"

        with open(file_path, "r", encoding="utf-8") as file:
            items = json.load(file)

        matches = []

        for item in items:
            if (
                item["type"].lower() == category.lower()
                and item["city"].lower() == city.lower()
                and item["price"] <= max_price
            ):
                matches.append(item)

        return {
            "status": "success",
            "output": matches,
            "error": None
        }

    except Exception as e:
        return {
            "status": "error",
            "output": None,
            "error": str(e)
        }
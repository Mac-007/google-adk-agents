import os
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. "
        "Please add your OpenRouter API key to the .env file."
    )


# ============================================================
# GET AVAILABLE OPENROUTER MODELS
# ============================================================

def get_available_models():
    """
    Get all models currently available on OpenRouter.
    """

    url = "https://openrouter.ai/api/v1/models"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("data", [])


# ============================================================
# FIND FREE MODELS THAT SUPPORT TOOLS
# ============================================================

def get_free_tool_models():
    """
    Return free OpenRouter models that support tool calling.
    """

    models = get_available_models()

    free_tool_models = []

    for model in models:

        model_id = model.get("id", "")

        pricing = model.get("pricing", {})

        prompt_price = pricing.get("prompt")
        completion_price = pricing.get("completion")

        supported_parameters = model.get(
            "supported_parameters",
            []
        )

        # Check if model is free.
        is_free = (
            prompt_price == "0"
            and completion_price == "0"
        )

        # Check if model supports tools.
        supports_tools = (
            "tools" in supported_parameters
        )

        if is_free and supports_tools:
            free_tool_models.append(model)

    return free_tool_models


# ============================================================
# SELECT MODEL
# ============================================================

def select_model():
    """
    Select a free model that supports tool calling.

    Returns:
        OpenRouter model ID.
    """

    models = get_free_tool_models()

    if not models:
        raise RuntimeError(
            "No free model with tool-calling support "
            "is currently available on OpenRouter."
        )

    # For now, simply select the first available model.
    selected_model = models[0]

    model_id = selected_model["id"]

    print(
        f"[MODEL SELECTOR] Selected model: {model_id}"
    )

    return model_id


# ============================================================
# TEST THIS FILE DIRECTLY
# ============================================================

if __name__ == "__main__":

    print("\nFree models supporting tools:")
    print("-" * 60)

    models = get_free_tool_models()

    for model in models:
        print(model["id"])

    print("-" * 60)

    selected = select_model()

    print(
        f"\nSelected model: {selected}"
    )
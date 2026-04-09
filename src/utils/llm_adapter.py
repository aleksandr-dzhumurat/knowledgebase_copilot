import os

from google import genai


class GeminiAdapter:
    """Adapter for Google Gemini API."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._client = genai.Client(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            vertexai=False,
        )

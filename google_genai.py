import os
from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
os.environ['GEMINI_API_KEY'] = 'AIzaSyBHenIdFOiNyIoyKBKG94O-A3lRoM_zEJU'
client = genai.Client()


def fetch_response(prompt: str, model: str = "gemini-2.5-flash") -> genai.types.GenerateContentResponse:
    response = client.models.generate_content(
        model=model, contents=prompt
    )
    return response

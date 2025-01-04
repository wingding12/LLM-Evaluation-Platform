import openai
from google.generativeai import GenerativeModel
import google.generativeai as genai
from .config import OPENAI_API_KEY, GOOGLE_API_KEY
from enum import Enum

class LLMProvider(Enum):
    GPT = "gpt-3.5-turbo"
    GEMINI = "gemini-pro"
    LLAMA = "llama-2-70b"
    FALCON = "falcon-40b"
    DONUT = "donut-2.7b"

class LLMService:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        genai.configure(api_key=GOOGLE_API_KEY)

    async def generate_response(self, model: str, system_prompt: str, user_message: str) -> str:
        try:
            if model.startswith("gpt"):
                return await self._call_openai(model, system_prompt, user_message)
            elif model == "gemini-pro":
                return await self._call_gemini(system_prompt, user_message)
            else:
                # For other models, implement their respective API calls
                raise NotImplementedError(f"Model {model} not implemented yet")
        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            return f"Error: {str(e)}"

    async def _call_openai(self, model: str, system_prompt: str, user_message: str) -> str:
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content

    async def _call_gemini(self, system_prompt: str, user_message: str) -> str:
        model = GenerativeModel('gemini-pro')
        response = await model.generate_content(
            f"{system_prompt}\n\nUser: {user_message}"
        )
        return response.text 
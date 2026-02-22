import asyncio
from typing import List, Optional

class GeminiClient:
    """Pequeño wrapper simulado para el SDK de Gemini.
    Reemplace con llamadas reales al SDK cuando tenga la key.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate(self, prompt: str, tools: Optional[List[str]] = None) -> str:
        # Placeholder: simula una llamada asíncrona al LLM
        await asyncio.sleep(0.01)
        return f"[LLM simulated response] Para: {prompt[:200]}"

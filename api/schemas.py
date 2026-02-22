from pydantic import BaseModel
from typing import Optional

# 1. Lo que recibimos de WhatsApp
class MessageRequest(BaseModel):
    user_id: str
    message: str

# 2. Lo que devolvemos al final del proceso
class MessageResponse(BaseModel):
    reply: str
    # Optional significa que puede ser texto o estar vacío (None)
    tool_used: Optional[str] = None

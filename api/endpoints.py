from fastapi import APIRouter, HTTPException
from api.schemas import MessageRequest, MessageResponse
# 1. Importamos nuestra función del Orchestrator
from core.orchestrator import process_message

# Creamos un "enrutador" que agrupará nuestras rutas relacionadas
router = APIRouter()

# Definimos que es un POST, la ruta "/message", y el tipo de respuesta esperada
@router.post("/message", response_model=MessageResponse)
async def handle_whatsapp_message(request: MessageRequest):
    """
    Recibe el mensaje de WhatsApp, lo procesa y devuelve la respuesta de la IA.
    """
    try:
        user_id = request.user_id
        user_message = request.message
        
        # 2. Le pasamos el mensaje al Orchestrator y esperamos (await) su respuesta
        respuesta_ia, tool_usada = await process_message(user_id, user_message)
        
        # 3. Empaquetamos la respuesta en el formato que espera WhatsApp
        return MessageResponse(
            reply=respuesta_ia,
            tool_used=tool_usada
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
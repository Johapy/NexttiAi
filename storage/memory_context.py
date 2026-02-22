from typing import List, Dict

# Diccionario global para guardar el historial temporalmente
# Formato: {"numero_telefono": [{"role": "user", "parts": ["hola"]}, ...]}
_chat_history: Dict[str, List[Dict]] = {}

def get_history(user_id: str) -> List[Dict]:
    """Recupera el historial de un usuario, o crea uno nuevo si no existe."""
    if user_id not in _chat_history:
        _chat_history[user_id] = []
    return _chat_history[user_id]

def add_message(user_id: str, role: str, text: str):
    """Añade un mensaje al historial respetando el formato de Gemini."""
    history = get_history(user_id)
    history.append({
        "role": role, # Puede ser "user" o "model"
        "parts": [{"text": text}]
    })
    
    # Mantenemos solo los últimos 20 mensajes para no saturar el contexto
    if len(history) > 20:
        _chat_history[user_id] = history[-20:]
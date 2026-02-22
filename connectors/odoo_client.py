import httpx
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None  # Guardaremos el UID aquí tras autenticar

    async def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Versión asíncrona de tu función json_rpc."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Odoo devuelve errores dentro del JSON 200 OK
                if "error" in data:
                    logger.error(f"Error en Odoo: {data['error']}")
                    raise Exception(data["error"].get("message", "Error desconocido en Odoo"))
                    
                return data
            except httpx.HTTPError as e:
                logger.error(f"Error HTTP conectando a Odoo: {str(e)}")
                raise

    async def authenticate(self) -> bool:
        """Autentica y guarda el UID en la instancia."""
        params = {
            "service": "common",
            "method": "authenticate",
            "args": [self.db, self.username, self.password, {}]
        }
        
        response = await self._call("call", params)
        self.uid = response.get("result")
        
        if self.uid:
            logger.info(f"Autenticado correctamente. UID: {self.uid}")
            return True
        return False

    async def execute(self, model: str, method: str, args: list):
        """Ejecuta un método genérico en cualquier modelo de Odoo."""
        
        # 1. Verificación de seguridad
        if not self.uid:
            raise Exception("No estás autenticado. Llama a authenticate() primero.")

        # 2. Construcción de los argumentos combinando listas
        full_args = [self.db, self.uid, self.password, model, method] + args
        
        # 3. Preparación del paquete (payload)
        params = {
            "service": "object",
            "method": "execute_kw",
            "args": full_args
        }
        
        # 4. Llamada al servidor y retorno de datos
        response = await self._call("call", params)
        return response.get("result")
# main.py
from fastapi import FastAPI
from api.endpoints import router

# 1. Inicializamos la aplicación principal de FastAPI
app = FastAPI(
    title="AI Orchestrator Odoo-Gemini",
    description="Microservicio para integrar WhatsApp, Gemini y Odoo"
)

# 2. Conectamos nuestras rutas (el router que creamos en endpoints.py)
app.include_router(router)

# 3. Configuramos Uvicorn para que arranque el servidor si ejecutamos este archivo directamente
if __name__ == "__main__":
    import uvicorn
    # "main:app" le dice a uvicorn que busque la variable 'app' en el archivo 'main'
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)

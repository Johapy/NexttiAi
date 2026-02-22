# core/orchestrator.py
from core.config import settings
from connectors.odoo_client import OdooClient
from storage.memory_context import get_history, add_message
from tools.definitions import tools_para_gemini
from tools.executors import execute_get_partner_by_phone, execute_get_top_selling_products, execute_get_total_sales_and_orders, execute_get_top_customers
from google import genai
from google.genai import types

# 1. Inicializamos nuestros clientes
odoo = OdooClient(
    url=settings.odoo_url, 
    db=settings.odoo_db, 
    username=settings.odoo_username, 
    password=settings.odoo_password
)

gemini_client = genai.Client(api_key=settings.gemini_api_key)

async def process_message(user_id: str, user_message: str):
    """Procesa el mensaje, consulta a Gemini y ejecuta tools si es necesario."""
    
    # Asegurarnos de que Odoo está conectado
    if not odoo.uid:
        await odoo.authenticate()

    # Guardamos el mensaje del usuario en la memoria
    add_message(user_id, "user", user_message)
    historial = get_history(user_id)

    # AQUÍ ENVIAMOS EL MENSAJE A GEMINI (Falta la lógica de respuesta)
    # ...
    # ... (código anterior del orchestrator) ...

    # 1. Enviamos el historial a Gemini indicándole qué herramientas existen
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=historial,
        config=types.GenerateContentConfig(tools=tools_para_gemini)
    )

    # 2. ¡Tu lógica aplicada aquí! Verificamos si pidió una herramienta
    if response.function_calls:
        # Gemini decidió que necesita usar una herramienta
        tool_call = response.function_calls[0]
        
        if tool_call.name == "get_partner_by_phone":
            phone = tool_call.args["phone_number"]
            resultado_odoo = await execute_get_partner_by_phone(odoo, phone)
            
            # 1. Le devolvemos el resultado al "chef" (Gemini)
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    # Añadimos el mensaje original de Gemini pidiendo la herramienta
                    response.candidates[0].content,
                    # Añadimos nuestra respuesta con los datos de Odoo
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="get_partner_by_phone",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            texto_final = respuesta_final_ia.text
            
            # 2. Guardamos en la memoria y devolvemos al usuario
            add_message(user_id, "model", texto_final)
            return texto_final, "get_partner_by_phone"
        
        # --- HERRAMIENTA 2: PRODUCTOS MÁS VENDIDOS ---
        elif tool_call.name == "get_top_selling_products":
            # Extraemos el límite si Gemini lo envió, si no, usamos 5 por defecto
            limite = int(tool_call.args.get("limit", 5))
            resultado_odoo = await execute_get_top_selling_products(odoo, limite)
            
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="get_top_selling_products",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            texto_final = respuesta_final_ia.text
            add_message(user_id, "model", texto_final)
            return texto_final, "get_top_selling_products"
        
        # --- HERRAMIENTA 3: TOTAL DE VENTAS Y PEDIDOS ---
        elif tool_call.name == "get_total_sales_and_orders":
            # Ejecutamos la función sin pasarle parámetros extra
            resultado_odoo = await execute_get_total_sales_and_orders(odoo)
            
            # Devolvemos los datos a la IA para que redacte el resumen
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="get_total_sales_and_orders",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            texto_final = respuesta_final_ia.text
            add_message(user_id, "model", texto_final)
            return texto_final, "get_total_sales_and_orders"
        
        # --- HERRAMIENTA 4: TOP CLIENTES CON MÁS VENTAS ---
        elif tool_call.name == "get_top_customers":
            # Extraemos el límite si Gemini lo envió; si no, usamos 10 por defecto
            limite = int(tool_call.args.get("limit", 10))
            
            # Ejecutamos la función pasándole el límite numérico
            resultado_odoo = await execute_get_top_customers(odoo, limite)
            
            # Devolvemos los datos a la IA
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="get_top_customers",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            texto_final = respuesta_final_ia.text
            add_message(user_id, "model", texto_final)
            return texto_final, "get_top_customers"

    else:
        # Si no hay function_calls, es un mensaje de texto normal
        respuesta_final = response.text
        
        # Guardamos la respuesta de la IA en la memoria
        add_message(user_id, "model", respuesta_final)
        
        return respuesta_final, None
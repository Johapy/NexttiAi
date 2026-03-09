# core/orchestrator.py
from core.config import settings
from connectors.odoo_client import OdooClient
from storage.memory_context import get_history, add_message
from tools.definitions import tools_para_gemini
from tools.executors import (
    execute_get_partner_by_phone, execute_get_top_selling_products, 
    execute_get_total_sales_and_orders, execute_get_top_customers, 
    execute_odoo_query, execute_create_odoo_record, 
    execute_update_odoo_record, execute_odoo_action
)
from google import genai
from google.genai import types

# 1. Inicializamos nuestros clientes
odoo = OdooClient(
    url=settings.odoo_url, 
    db=settings.odoo_db, 
    username=settings.odoo_username, 
    password=settings.odoo_password
)

mapa_odoo = """
Crea mensajes cortos limpios y bien organizados y en formato markdown para responder a las preguntas del usuario sobre su empresa, usando los datos que tienes en Odoo.

ESTRUCTURA DE LA BASE DE DATOS (ODOO MAP):
Para responder preguntas con la herramienta 'execute_odoo_query', usa estos modelos y métodos:
- 'stock.quant': Contiene el inventario de productos. (Campos: product_id, quantity, location_id).
- 'res.partner': Contiene clientes y contactos. (Campos: name, phone, email).
- 'sale.order': Contiene los pedidos de venta. (Campos: name, partner_id, amount_total, state).
- 'product.product': Contiene los productos. (Campos: name, list_price, qty_available).
- 'crm.lead': Contiene las iniciativas y oportunidades del CRM. (Campos: name, partner_id, stage_id, expected_revenue, probability, type, priority, description).
- 'account.account' (Plan de Cuentas). Campos: code, name, account_type, current_balance.
- 'account.move.line' (Apuntes Contables). Campos: account_id, balance, debit, credit.
- 'account.move' (Facturas y Contabilidad). Campos clave: name, partner_id, amount_total, state, move_type, payment_state.

MÉTODOS PERMITIDOS Y REGLAS:
- 'search_read': Para buscar listas de registros.
- 'search_count': Para contar la cantidad de registros.
- 'read_group': Para agrupar y sumar. ¡IMPORTANTE! DEBES enviar 'groupby' (ej. ['stage_id']) y 'fields' (ej. ['stage_id', 'expected_revenue']).

HERRAMIENTAS Y REGLAS:
1. 'execute_odoo_query': Solo para LEER.
2. 'create_odoo_record': Para CREAR registros. NUNCA inventes IDs.
3. 'update_odoo_record': Para ACTUALIZAR registros.
   - REGLA DE ORO: NO uses esta herramienta para "Confirmar" pedidos o "Publicar" facturas. Solo úsala para actualizar texto, números o fechas.
4. 'execute_odoo_action': Para EJECUTAR acciones de negocio (botones). 
   - Para CONFIRMAR un pedido de venta ('sale.order'), usa 'action_confirm'.
   - Para PUBLICAR/VALIDAR una factura ('account.move'), usa 'action_post'.
"""

gemini_client = genai.Client(api_key=settings.gemini_api_key)

async def process_message(user_id: str, user_message: str):
    """Procesa el mensaje mediante un Bucle de Agente Autónomo."""
    
    if not odoo.uid:
        await odoo.authenticate()
        print(f"🔑 Intento de conexión a Odoo. UID obtenido: {odoo.uid}")

    add_message(user_id, "user", user_message)
    historial = get_history(user_id)

    # 🔄 EL BUCLE DE RAZONAMIENTO: La IA puede dar hasta 5 vueltas buscando información
    for paso in range(5):
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=historial,
            config=types.GenerateContentConfig(
                tools=tools_para_gemini,
                system_instruction=mapa_odoo
            )
        )

        if response.function_calls:
            tool_call = response.function_calls[0]
            nombre = tool_call.name
            print(f"\n🔄 Paso {paso+1}: La IA decidió usar la herramienta '{nombre}'")
            
            # --- EJECUCIÓN CENTRALIZADA DE HERRAMIENTAS ---
            if nombre == "get_partner_by_phone":
                phone = tool_call.args.get("phone_number")
                resultado_odoo = await execute_get_partner_by_phone(odoo, phone)
                
            elif nombre == "get_top_selling_products":
                limite = int(tool_call.args.get("limit", 5))
                resultado_odoo = await execute_get_top_selling_products(odoo, limite)
                
            elif nombre == "get_total_sales_and_orders":
                resultado_odoo = await execute_get_total_sales_and_orders(odoo)
                
            elif nombre == "get_top_customers":
                limite = int(tool_call.args.get("limit", 10))
                resultado_odoo = await execute_get_top_customers(odoo, limite)

            elif nombre == "execute_odoo_query":
                modelo = tool_call.args.get("model")
                metodo = tool_call.args.get("method")
                dominio = tool_call.args.get("domain", [])
                campos = tool_call.args.get("fields", [])
                groupby = tool_call.args.get("groupby", [])
                limite = int(tool_call.args.get("limit", 15))
                resultado_odoo = await execute_odoo_query(odoo, modelo, metodo, dominio, campos, limite, groupby)

            elif nombre == "create_odoo_record":
                modelo = tool_call.args.get("model")
                valores = tool_call.args.get("values", {})
                resultado_odoo = await execute_create_odoo_record(odoo, modelo, valores)

            elif nombre == "update_odoo_record":
                modelo = tool_call.args.get("model")
                record_id = int(tool_call.args.get("record_id"))
                valores = tool_call.args.get("values", {})
                resultado_odoo = await execute_update_odoo_record(odoo, modelo, record_id, valores)

            elif nombre == "execute_odoo_action":
                modelo = tool_call.args.get("model")
                metodo = tool_call.args.get("method")
                record_ids = tool_call.args.get("record_ids", [])
                resultado_odoo = await execute_odoo_action(odoo, modelo, metodo, record_ids)

            else:
                mensaje_error = f"Herramienta desconocida: '{nombre}'"
                print(f"🚨 ATENCIÓN: {mensaje_error}")
                resultado_odoo = {"error": mensaje_error}

            # Añadimos la petición y el resultado al historial temporal, y el bucle sigue girando ♻️
            historial.append(response.candidates[0].content)
            historial.append(
                types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(
                        name=nombre,
                        response=resultado_odoo
                    )]
                )
            )

        else:
            # ✅ Si ya no hay function_calls, la IA está lista para hablar
            texto_final = response.text if response.text else "Proceso completado exitosamente."
            print("✅ La IA ha terminado de pensar y redactó su respuesta.")
            
            add_message(user_id, "model", texto_final)
            return texto_final, "proceso_exitoso"

    # 🛑 Si da 5 vueltas y no termina, cortamos por seguridad
    mensaje_limite = "He analizado varios datos, pero el proceso es muy extenso. ¿Podrías hacerme una pregunta más específica?"
    add_message(user_id, "model", mensaje_limite)
    return mensaje_limite, "limite_de_pasos_alcanzado"
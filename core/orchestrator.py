# core/orchestrator.py
from core.config import settings
from connectors.odoo_client import OdooClient
from storage.memory_context import get_history, add_message
from tools.definitions import tools_para_gemini
from tools.executors import execute_get_partner_by_phone, execute_get_top_selling_products, execute_get_total_sales_and_orders, execute_get_top_customers, execute_odoo_query, execute_create_odoo_record, execute_update_odoo_record
from google import genai
from google.genai import types

# 1. Inicializamos nuestros clientes
odoo = OdooClient(
    url=settings.odoo_url, 
    db=settings.odoo_db, 
    username=settings.odoo_username, 
    password=settings.odoo_password
)

mapa_odoo = mapa_odoo = """
Crea mensajes cortos limpios y bien organizados y en formato markdown para responder a las preguntas del usuario sobre su empresa, usando los datos que tienes en Odoo.

ESTRUCTURA DE LA BASE DE DATOS (ODOO MAP):
Para responder preguntas con la herramienta 'execute_odoo_query', usa estos modelos y métodos:
- 'stock.quant': Contiene el inventario de productos. (Campos: product_id, quantity, location_id).
- 'res.partner': Contiene clientes y contactos. (Campos: name, phone, email).
- 'sale.order': Contiene los pedidos de venta. (Campos: name, partner_id, amount_total, state).
- 'product.product': Contiene los productos. (Campos: name, list_price, qty_available).
- 'crm.lead': Contiene las iniciativas y oportunidades del CRM. (Campos: name, partner_id, stage_id, expected_revenue, probability, type, priority(ajusta del 1 a 3 y 0 si no es importante), description).
- 'account.account' (Plan de Cuentas). Campos: code, name, account_type (ej. 'asset_current' para Activos Corrientes, 'liability_current' para Pasivos), current_balance.
- 'account.move.line' (Apuntes Contables). Campos: account_id, balance, debit, credit. (Ideal para sumar el balance real agrupando por cuenta).
- 'account.move' (Facturas y Contabilidad). Campos clave: 
  * 'name': Número de factura.
  * 'partner_id': Cliente.
  * 'amount_total': Total de la factura.
  * 'state': Estado ('draft' es borrador, 'posted' es publicada/validada).
  * 'move_type': 'out_invoice' (Factura de cliente), 'in_invoice' (Factura de proveedor).
  * 'payment_state': 'not_paid' (No pagada), 'paid' (Pagada), 'partial' (Pago parcial).

MÉTODOS PERMITIDOS Y REGLAS:
- 'search_read': Para buscar listas de registros.
- 'search_count': Para contar la cantidad de registros.
- 'read_group': Para agrupar y sumar. ¡IMPORTANTE! Si usas 'read_group', DEBES enviar obligatoriamente los parámetros 'groupby' (ej. ['stage_id']) y 'fields' (ej. ['stage_id', 'expected_revenue']).

HERRAMIENTAS Y REGLAS:
1. 'execute_odoo_query': Solo para LEER. Métodos: 'search_read', 'search_count', 'read_group'.
2. 'create_odoo_record': Para CREAR registros. Usa el modelo correspondiente y pasa los campos en el parámetro 'values'. NUNCA inventes IDs.
3. 'update_odoo_record': Para ACTUALIZAR registros. Usa siempre el ID del registro. 
   - Puedes usarlo para actualizar precios ('list_price' en 'product.product').
   - Puedes usarlo para actualizar datos de clientes ('phone', 'email' en 'res.partner').
   - Para cambiar el estado del CRM, usa 'stage_id' con el número.
   - REGLA DE ORO: NO uses esta herramienta para "Confirmar" pedidos de venta o "Publicar" facturas. Solo úsala para actualizar información de texto, números o fechas.
"""

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
        config=types.GenerateContentConfig(
            tools=tools_para_gemini,
            system_instruction=mapa_odoo  # ¡Aquí inyectamos el mapa!
        )
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
        
        # --- NUEVA HERRAMIENTA: CREAR REGISTROS ---
        elif tool_call.name == "create_odoo_record":
            modelo = tool_call.args.get("model")
            # Extraemos el diccionario de valores que armó la IA
            valores = tool_call.args.get("values", {})
            
            resultado_odoo = await execute_create_odoo_record(odoo, modelo, valores)
            
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="create_odoo_record",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            if respuesta_final_ia.text:
                texto_final = respuesta_final_ia.text
            else:
                texto_final = "Registro creado con éxito, pero la IA no generó texto de confirmación."
                
            add_message(user_id, "model", texto_final)
            return texto_final, "create_odoo_record"
        
        # --- HERRAMIENTA: ACTUALIZAR REGISTROS ---
        elif tool_call.name == "update_odoo_record":
            modelo = tool_call.args.get("model")
            record_id = int(tool_call.args.get("record_id"))
            valores = tool_call.args.get("values", {})
            
            resultado_odoo = await execute_update_odoo_record(odoo, modelo, record_id, valores)
            
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="update_odoo_record",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            texto_final = respuesta_final_ia.text if respuesta_final_ia.text else "Registro actualizado con éxito."
            add_message(user_id, "model", texto_final)
            return texto_final, "update_odoo_record"
        
        # --- HERRAMIENTA UNIVERSAL: CONSULTAS DINÁMICAS ---
        elif tool_call.name == "execute_odoo_query":
            modelo = tool_call.args.get("model")
            metodo = tool_call.args.get("method")
            dominio = tool_call.args.get("domain", [])
            campos = tool_call.args.get("fields", [])
            groupby = tool_call.args.get("groupby", []) # <--- Extraemos groupby
            limite = int(tool_call.args.get("limit", 15))
            
            # Pasamos groupby a la función
            resultado_odoo = await execute_odoo_query(odoo, modelo, metodo, dominio, campos, limite, groupby)
            
            respuesta_final_ia = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=historial + [
                    response.candidates[0].content,
                    types.Content(
                        role="tool",
                        parts=[types.Part.from_function_response(
                            name="execute_odoo_query",
                            response=resultado_odoo
                        )]
                    )
                ]
            )

            # 🛡️ NUEVO SALVAVIDAS PARA EL TEXTO:
            if respuesta_final_ia.text:
                texto_final = respuesta_final_ia.text
            else:
                texto_final = "La IA procesó los datos de Odoo, pero no pudo generar una respuesta de texto (posiblemente intentó encadenar otra herramienta)."
                print(f"Respuesta cruda de la IA sin texto: {respuesta_final_ia}") # Para depurar
                
            add_message(user_id, "model", texto_final)
            return texto_final, "execute_odoo_query"
        # 🚨 SALVAVIDAS:
        else:
            # Si Gemini inventa una herramienta, lo atrapamos aquí
            mensaje_error = f"Error: La IA intentó usar una herramienta desconocida llamada '{tool_call.name}'"
            print(f"ATENCIÓN: {mensaje_error}")
            return mensaje_error, "herramienta_desconocida"

    else:
        # Si no hay function_calls, es un mensaje de texto normal
        respuesta_final = response.text
        
        # Guardamos la respuesta de la IA en la memoria
        add_message(user_id, "model", respuesta_final)
        
        return respuesta_final, None
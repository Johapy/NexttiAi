# tools/executors.py
from typing import Dict, Any


async def execute_odoo_action(odoo_client, model: str, method: str, record_ids: list) -> dict:
    """Ejecuta un método de negocio específico en Odoo (como apretar un botón)."""
    try:
        # Los métodos de acción en Odoo reciben una lista de IDs como primer argumento posicional.
        # Por lo tanto, empaquetamos record_ids dentro de otra lista: [record_ids]
        resultado = await odoo_client.execute(model, method, [record_ids])
        
        # Odoo suele devolver True o un diccionario (acción de ventana) si fue exitoso
        if resultado is not False:
            return {
                "status": "success", 
                "message": f"Acción '{method}' ejecutada correctamente en los registros {record_ids} del modelo {model}."
            }
            
        return {"status": "error", "message": f"Odoo devolvió False al intentar ejecutar '{method}'."}
        
    except Exception as e:
        return {"status": "error", "message": f"Error en Odoo al ejecutar acción: {str(e)[:150]}"}

# tools/executors.py
async def execute_update_odoo_record(odoo_client, model: str, record_id: int, values: dict) -> dict:
    """Actualiza un registro existente en Odoo."""
    try:
        # 1. Los datos posicionales: una lista con los IDs y el diccionario de valores
        argumentos_posicionales = [[record_id], values]
        # 2. Las opciones extra (kwargs): un diccionario vacío
        opciones_extra = {}
        
        # Empaquetamos todo exactamente como el cliente de Odoo lo exige
        args_para_odoo = [argumentos_posicionales, opciones_extra]
        
        resultado = await odoo_client.execute(model, 'write', args_para_odoo)
        
        if resultado:
            return {"status": "success", "message": f"Registro {record_id} en {model} actualizado correctamente."}
            
        return {"status": "error", "message": "Odoo devolvió False. No se pudo actualizar el registro."}
        
    except Exception as e:
        return {"status": "error", "message": f"Error en Odoo al actualizar: {str(e)[:150]}"}

async def execute_create_odoo_record(odoo_client, model: str, values: dict) -> dict:
    """Crea un nuevo registro en Odoo de forma autónoma."""
    try:
        # 🛠️ LA SOLUCIÓN: Doble corchete [[values]]
        # El primer corchete es la lista de argumentos (args) de XML-RPC.
        # El segundo corchete es la lista de registros que Odoo exige para el método 'create'.
        record_id = await odoo_client.execute(model, 'create', [[values]])
        
        if record_id:
            # Odoo devuelve una lista con los IDs creados, extraemos el primero
            id_creado = record_id[0] if isinstance(record_id, list) else record_id
            return {
                "status": "success", 
                "message": f"Registro creado exitosamente en {model}.", 
                "record_id": id_creado
            }
            
        return {"status": "error", "message": "No se recibió un ID al intentar crear el registro."}
          
    except Exception as e:
        return {"status": "error", "message": f"Error en Odoo al crear: {str(e)[:150]}"}

async def execute_odoo_query(odoo_client, model: str, method: str, domain: list = None, fields: list = None, limit: int = 15, groupby: list = None) -> dict:
    """Ejecuta una consulta dinámica en Odoo según los parámetros recibidos."""
    
    # 🛡️ 1. GUARDIA DE SEGURIDAD: Bloqueamos métodos peligrosos y agregamos 'read_group'
    metodos_permitidos = ['search_read', 'search_count', 'read_group']
    if method not in metodos_permitidos:
        return {"status": "error", "message": f"Por seguridad, el método '{method}' no está permitido."}

    if domain is None:
        domain = []

    # 2. Preparamos las opciones extra (kwargs)
    opciones = {}
    if fields:
        opciones['fields'] = fields
        
    # Agregamos groupby SOLO si el método es read_group (evita errores en Odoo)
    if groupby and method == 'read_group':
        opciones['groupby'] = groupby
        
    # El límite ahora aplica tanto para listas como para agrupaciones
    if limit and method in ['search_read', 'read_group']:
        opciones['limit'] = limit

    # 3. Empaquetamos todo para Odoo
    args = [ [domain], opciones ]
    
    try:
        result = await odoo_client.execute(model, method, args)
        if result is not None:
            return {"status": "success", "data": result}
        return {"status": "not_found", "message": "No se encontraron datos."}
    except Exception as e:
        # Simplificamos el error para que Gemini no se confunda
        return {"status": "error", "message": f"Error en Odoo: {str(e)[:100]}"}

async def execute_get_top_customers(odoo_client, limit: int = 10) -> Dict[str, Any]:
    """Obtiene los clientes con el mayor volumen de compras."""
    # 1. Filtramos solo ventas confirmadas
    domain_ventas = [['state', 'in', ['sale', 'done']]]
    
    # 2. Preparamos los argumentos, envolviendo el dominio en una lista extra
    args = [
        [domain_ventas], 
        {
            'fields': ['partner_id', 'amount_total'], 
            'groupby': ['partner_id'],                
            'orderby': 'amount_total desc',           
            'limit': limit  # Usamos la variable que define Gemini
        }
    ]
    
    try:
        # 3. Llamada a Odoo usando 'sale.order' y 'read_group'
        result = await odoo_client.execute('sale.order', 'read_group', args)
        
        # 4. Retornamos los datos
        if result:
            return {"status": "success", "data": result}
        return {"status": "not_found", "message": "No se encontraron ventas confirmadas."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def execute_get_total_sales_and_orders(odoo_client) -> Dict[str, Any]:
    """Obtiene el saldo total de ventas y número de pedidos."""
    domain_confirmadas = [['state', 'in', ['sale', 'done']]]
    
    # Envolvemos el dominio en una lista extra [domain_confirmadas]
    args = [
        [domain_confirmadas], 
        {
            'fields': ['amount_total'], 
            'groupby': [] 
        }
    ]
    
    try:
        # Ejecutamos en el modelo 'sale.order' con el método 'read_group'
        result = await odoo_client.execute('sale.order', 'read_group', args)
        
        if result:
            total_dinero = result[0].get('amount_total', 0)
            count_pedidos = result[0].get('__count', 0)
            
            return {
                "status": "success", 
                "data": {
                    "total_sales": total_dinero,
                    "total_orders": count_pedidos
                }
            }
        return {"status": "not_found", "message": "No hay ventas registradas."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def execute_get_top_selling_products(odoo_client, limit: int = 5) -> Dict[str, Any]:
    """Obtiene los productos más vendidos."""
    domain = [['state', 'in', ['sale', 'done']]]
    
    args = [
        [domain], # Nuestra lista extra para que Odoo lo lea bien
        {
            'fields': ['product_id', 'product_uom_qty'], 
            'groupby': ['product_id'], 
            'orderby': 'product_uom_qty desc',
            'limit': limit # Usamos el número que decida Gemini (o 5 por defecto)
        }
    ]
    
    try:
        # 3. ¡LA LLAMADA A ODOO!
        # Pasamos exactamente el modelo ('sale.order.line') y el método ('read_group')
        result = await odoo_client.execute('sale.order.line', 'read_group', args)
        
        # 4. Formateamos la respuesta para Gemini
        if result:
            return {"status": "success", "data": result}
        return {"status": "not_found", "message": "No hay datos de productos vendidos."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def execute_get_partner_by_phone(odoo_client, phone_number: str) -> Dict[str, Any]:
    """Busca un cliente en Odoo por su teléfono."""
    
    # 1. Construimos el filtro (dominio) exactamente como Odoo lo exige
    domain = [['phone', '=', phone_number]]
    
    # 2. Preparamos los argumentos: el filtro, los campos que queremos y el límite
    args = [
        [domain], # 🛠️ ¡Aquí está el cambio! Envolvemos domain en una lista nueva
        {
            'fields': ['id', 'name', 'phone'], 
            'limit': 1
        }
    ]
    
    try:
        # 3. Llamamos a nuestro método genérico
        # Modelo: 'res.partner', Método: 'search_read'
        result = await odoo_client.execute('res.partner', 'search_read', args)
        
        # 4. Devolvemos el resultado estructurado para que Gemini lo entienda
        if result:
            return {"status": "success", "data": result[0]}
        return {"status": "not_found", "message": "No se encontró ningún cliente con ese número."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
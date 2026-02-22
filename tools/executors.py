# tools/executors.py
from typing import Dict, Any

# tools/executors.py

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
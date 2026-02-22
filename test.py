import requests
import json
import re

url = "https://nextticlientes-demostracionesv19-qa-27956445.dev.odoo.com/jsonrpc"
db = "nextticlientes-demostracionesv19-qa-27956445"
username = "info@nexttisolutions.com"
password = "123"

def json_rpc(url, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    return requests.post(url, json=data).json()

def clean_html(raw_html):
    """Limpia etiquetas HTML básicas para dejar solo texto plano para la IA"""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

try:
    uid_response = json_rpc(url, "call", {"service": "common", "method": "authenticate", "args": [db, username, password, {}]})
    uid = uid_response.get("result")

    if uid:
        print(f"Conectado correctamente. UID: {uid}\n")

        # 1. Filtramos solo los mensajes de los canales de chat
        # Nota: Si usas Odoo 17+, cambia 'mail.channel' por 'discuss.channel'
        domain = [['model', 'in', ['mail.channel', 'discuss.channel']]] 

        search_params = {
            "service": "object",
            "method": "execute_kw",
            "args": [db, uid, password, 'mail.message', 'search_read', 
                [domain], 
                {
                    # 2. Agregamos 'res_id' que es el ID del canal/chat
                    'fields': ['id', 'author_id', 'body', 'create_date', 'model', 'res_id'], 
                    'limit': 100,
                    'order': 'id asc' # 3. Orden ascendente (del más viejo al más nuevo) para el historial
                }
            ]
        }

        messages = json_rpc(url, "call", search_params).get("result", [])

        if messages:
            # Diccionario para agrupar los chats por sesión/usuario
            conversaciones = {}

            for msg in messages:
                chat_id = msg.get('res_id')
                if not chat_id:
                    continue
                
                # Inicializar la lista de la conversación si no existe
                if chat_id not in conversaciones:
                    conversaciones[chat_id] = []

                # Identificar al autor
                author_data = msg.get('author_id')
                if isinstance(author_data, list) and len(author_data) > 1:
                    autor = author_data[1]
                else:
                    autor = "Visitante"

                # Limpieza de Body
                body_clean = clean_html(msg.get('body'))

                # Evitar agregar mensajes vacíos del sistema
                if body_clean:
                    # Estructura pensada para que una IA lo consuma
                    conversaciones[chat_id].append({
                        "role": "user" if autor == "Visitante" else "assistant",
                        "autor_real": autor,
                        "content": body_clean,
                        "timestamp": msg.get('create_date')
                    })

            # Imprimir el resultado agrupado
            for chat_id, historial in conversaciones.items():
                print(f"--- SESIÓN DE CHAT ID: {chat_id} ---")
                for linea in historial:
                    print(f"[{linea['role'].upper()}] {linea['autor_real']}: {linea['content']}")
                print("\n")
                
        else:
            print("No se encontraron mensajes de Livechat.")

        # ==========================================
        # BLOQUE 2: TOP 10 CLIENTES CON MÁS VENTAS
        # ==========================================
        print("=== EXTRAYENDO TOP 10 VENTAS GLOBALES ===")
        domain_ventas = [['state', 'in', ['sale', 'done']]]
        
        group_params = {
            "service": "object",
            "method": "execute_kw",
            "args": [
                db, uid, password, 
                'sale.order',       
                'read_group',       
                [domain_ventas],    
                {
                    'fields': ['partner_id', 'amount_total'], 
                    'groupby': ['partner_id'],                
                    'orderby': 'amount_total desc',           
                    'limit': 10                               
                }
            ]
        }

        top_clientes = json_rpc(url, "call", group_params).get("result", [])

        if top_clientes:
            print("\n" + "="*55)
            print(f"{'TOP 10 CLIENTES CON MÁS VENTAS':^55}")
            print("="*55)
            print(f"{'CLIENTE':<35} | {'TOTAL COMPRADO'}")
            print("-" * 55)
            
            for cliente in top_clientes:
                datos_cliente = cliente.get('partner_id')
                nombre = datos_cliente[1] if isinstance(datos_cliente, list) else "Desconocido"
                total_comprado = cliente.get('amount_total', 0.0)
                
                print(f"{nombre[:30]:<35} | ${total_comprado:,.2f}")
        else:
            print("No se encontraron ventas confirmadas para agrupar.")

        # ==========================================
        # BLOQUE 3: SALDO TOTAL DE VENTAS (GLOBAL)
        # ==========================================
        print("=== CALCULANDO SALDO TOTAL DE VENTAS ===")
        
        # Filtro: Solo ventas confirmadas
        domain_confirmadas = [['state', 'in', ['sale', 'done']]]
        
        ventas_globales = json_rpc(url, "call", {
            "service": "object",
            "method": "execute_kw",
            "args": [db, uid, password, 'sale.order', 'read_group', 
                [domain_confirmadas], 
                {'fields': ['amount_total'], 'groupby': []} # Groupby vacío = Total General
            ]
        }).get("result", [])

        if ventas_globales:
            total_dinero = ventas_globales[0].get('amount_total', 0)
            count_pedidos = ventas_globales[0].get('__count', 0)
            print(f"💰 Saldo Total en Ventas: ${total_dinero:,.2f}")
            print(f"📦 Número Total de Pedidos: {count_pedidos}")
        
        print("\n")

        # ==========================================
        # BLOQUE 4: EL PRODUCTO MÁS VENDIDO (TOP 5)
        # ==========================================
        print("=== TOP 5 PRODUCTOS MÁS VENDIDOS ===")
        
        # Consultamos las líneas de pedido (sale.order.line)
        # Filtramos para que solo cuente líneas de pedidos confirmados
        domain_lineas = [['state', 'in', ['sale', 'done']]]
        
        productos_top = json_rpc(url, "call", {
            "service": "object",
            "method": "execute_kw",
            "args": [db, uid, password, 'sale.order.line', 'read_group', 
                [domain_lineas], 
                {
                    'fields': ['product_id', 'product_uom_qty'], 
                    'groupby': ['product_id'], 
                    'orderby': 'product_uom_qty desc', # Ordenar por cantidad vendida
                    'limit': 5
                }
            ]
        }).get("result", [])

        if productos_top:
            print(f"{'PRODUCTO':<35} | {'CANTIDAD VENDIDA'}")
            print("-" * 55)
            for prod in productos_top:
                nombre_prod = prod.get('product_id')[1] if prod.get('product_id') else "Desconocido"
                cantidad = prod.get('product_uom_qty', 0)
                print(f"{nombre_prod[:30]:<35} | {int(cantidad)} unidades")
        else:
            print("No hay datos de productos vendidos.")

    else:
        print("Error de autenticación.")

except Exception as e:
    print(f"Error: {e}")
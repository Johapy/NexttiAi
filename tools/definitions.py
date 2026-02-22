# tools/definitions.py

# Definimos la herramienta con la estructura que Gemini entiende (OpenAPI schema)
tools_para_gemini = [
    {
        "function_declarations": [
            {
                "name": "get_partner_by_phone",
                "description": "Busca un cliente en el sistema Odoo usando su número de teléfono para saber su ID y su nombre.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "phone_number": {
                            "type": "STRING",
                            "description": "El número de teléfono del cliente. Ej: +521234567890"
                        }
                    },
                    "required": ["phone_number"]
                }
            },
            {
                "name": "get_top_selling_products",
                "description": "Obtiene la lista de los productos más vendidos en el sistema Odoo. Útil cuando el usuario pregunta por los top ventas o los productos más populares.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "limit": {
                            "type": "INTEGER",
                            "description": "La cantidad de productos top a devolver. Ej: 5 para el top 5. Si el usuario no especifica, usar 5."
                        }
                    }
                }
            },
            {
                "name": "get_total_sales_and_orders",
                "description": "Obtiene el saldo total de dinero en ventas confirmadas y el número total de pedidos en el sistema. Útil para dar un resumen general financiero o de rendimiento de la empresa."
            },
            {
                "name": "get_top_customers",
                "description": "Obtiene la lista de los clientes con el mayor volumen de compras acumuladas. Útil cuando el usuario pregunta por los mejores clientes o el top de ventas por cliente.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "limit": {
                            "type": "INTEGER",
                            "description": "La cantidad de clientes del top a devolver. Ej: 3 para los 3 mejores. Si el usuario no especifica, usar 10."
                        }
                    }
                }
            }
        ]
    }
]
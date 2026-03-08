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
            },
            {
                "name": "execute_odoo_query",
                "description": "Herramienta universal para buscar, contar o leer registros en Odoo.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "model": {
                            "type": "STRING",
                            "description": "El modelo a consultar (ej. 'res.partner')."
                        },
                        "method": {
                            "type": "STRING",
                            "description": "Usa 'search_read' para obtener listas de datos o 'search_count' para contar cantidad de registros."
                        },
                        "domain": {
                            "type": "ARRAY",
                            "description": "Filtros en formato Odoo (ej. [['state', '=', 'sale']]).",
                            "items": {"type": "STRING"} 
                        },
                        "fields": {
                            "type": "ARRAY",
                            "description": "Lista de campos a devolver (ej. ['partner_id', 'amount_total']).",
                            "items": {"type": "STRING"}
                        },
                        "groupby": {
                            "type": "ARRAY",
                            "description": "Lista de campos para agrupar (ej. ['partner_id']). Solo se usa con 'read_group'.",
                            "items": {"type": "STRING"}
                        },
                        "limit": {
                            "type": "INTEGER",
                            "description": "Límite de registros (por defecto 10)."
                        }
                    },
                    "required": ["model", "method"]
                }
            },
            {
                "name": "create_odoo_record",
                "description": "Herramienta para crear nuevos registros en Odoo (como clientes, contactos o iniciativas en el CRM).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "model": {
                            "type": "STRING",
                            "description": "El modelo donde se creará el registro (ej. 'res.partner', 'crm.lead')."
                        },
                        "values": {
                            "type": "OBJECT",
                            "description": "Diccionario con los campos y valores a insertar (ej. {'name': 'Juan Perez', 'phone': '+123456', 'email': 'juan@mail.com'})."
                        }
                    },
                    "required": ["model", "values"]
                }
            },
            {
                "name": "update_odoo_record",
                "description": "Herramienta para actualizar o modificar registros existentes en Odoo (ej. cambiar el estado de un lead, actualizar un teléfono).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "model": {
                            "type": "STRING",
                            "description": "El modelo del registro (ej. 'crm.lead')."
                        },
                        "record_id": {
                            "type": "INTEGER",
                            "description": "El ID numérico del registro que se va a actualizar."
                        },
                        "values": {
                            "type": "OBJECT",
                            "description": "Diccionario con los campos y sus nuevos valores (ej. {'stage_id': 3, 'phone': '12345'})."
                        }
                    },
                    "required": ["model", "record_id", "values"]
                }
            }
        ]
    }
]
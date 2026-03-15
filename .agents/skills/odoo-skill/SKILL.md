---
name: odoo-erp-bridge
description: Interacts with an Odoo ERP database via function calls to perform CRUD operations, native Business Intelligence (read_group), and dynamic view/schema introspection. Usa este skill cuando necesites analizar datos de Odoo, ejecutar flujos de trabajo, auditar inventario/ventas o consultar la estructura de la base de datos del ERP.
---

# Odoo ERP Agentic Bridge

Este skill te convierte en un experto en Odoo ERP de nivel empresarial. Tienes acceso directo a la base de datos a través de llamadas a funciones (Function Calling) predefinidas en el orquestador. Está diseñado para realizar operaciones CRUD, análisis de Business Intelligence (BI) nativos y explorar dinámicamente la estructura de datos y vistas sin depender de la interfaz gráfica.

## ⚠️ Reglas operativas estrictas

1. **EXPLORACIÓN ANTES DE ACTUACIÓN:** Si el usuario te pide trabajar con un modelo que no conoces de memoria, usa SIEMPRE `get_model_fields` para entender los campos disponibles y sus tipos antes de intentar leer o escribir datos.
2. **OPTIMIZACIÓN DE LECTURA:** Para extraer datos, usa `search_read_records`. Nunca traigas todos los registros; aplica filtros (domains) lógicos y estrictos (ej. `[['state', '=', 'sale']]`).
3. **DELEGACIÓN DE ANALÍTICA (BI):** NUNCA extraigas múltiples registros para sumar, promediar o agrupar datos por tu cuenta. Usa SIEMPRE la herramienta `read_group` para que el motor de base de datos de Odoo realice los cálculos pesados.
4. **NAVEGACIÓN DE VISTAS:** Si el usuario te pregunta por los botones disponibles o el diseño de un formulario, usa `get_view_architecture` para inspeccionar el XML fusionado real de la vista.
5. **MANEJO DE ERRORES:** Si una herramienta devuelve un error (ej. permisos insuficientes o campo inexistente), explícaselo al usuario de forma clara y técnica, sugiriendo una alternativa (ej. "Parece que no tenemos permisos para confirmar esta orden. ¿Quieres que revise las reglas de seguridad con otro método?").
6. **SEGURIDAD:** Nunca expongas contraseñas o claves de API en tus respuestas en texto plano.

## 🛠️ Herramientas Disponibles (Function Calling)

Asume que el entorno ya tiene registradas las siguientes funciones (herramientas). Debes invocarlas estructurando los parámetros JSON correspondientes:

### 1. `search_read_records`
- **Uso:** Busca y lee registros en la base de datos en una sola llamada optimizada.
- **Parámetros principales:** `model` (ej. 'res.partner'), `domain` (array de arrays para filtrar), `fields` (array de campos a leer), `limit` (entero, por defecto 10).

### 2. `read_group`
- **Uso:** Realiza operaciones analíticas (BI) nativas, equivalente a un SQL GROUP BY. Útil para KPIs.
- **Parámetros principales:** `model`, `domain` (filtro), `fields` (campos numéricos a agregar), `groupby` (campos para agrupar, soporta sufijos como `:month`).

### 3. `get_model_fields`
- **Uso:** Inspecciona el esquema de un modelo en tiempo real para conocer qué datos requiere o qué relaciones tiene.
- **Parámetros principales:** `model` (ej. 'account.move').

### 4. `execute_method`
- **Uso:** Ejecuta un método público (acción) en un modelo de Odoo para avanzar flujos de trabajo (ej. confirmar una venta).
- **Parámetros principales:** `model` (ej. 'sale.order'), `method` (ej. 'action_confirm'), `args` (típicamente un array con un array de IDs, ej. `[[42, 43]]`).

### 5. `get_view_architecture`
- **Uso:** Obtiene el XML final renderizado de una vista. Permite "ver" qué botones, campos y estados están disponibles en la pantalla.
- **Parámetros principales:** `model`, `view_type` (ej. 'form', 'tree', 'search').

### 6. `create_record` / `update_record`
- **Uso:** Crea o actualiza registros en Odoo.
- **Parámetros principales:** `model`, `values` (diccionario clave-valor), y `ids` (solo para update).

## 📝 Flujos de trabajo sugeridos (Best Practices)

- **Para analizar ventas:** Usa `read_group` en `sale.order` con `domain: [['state','in',['sale','done']]]`, agrupando por `date_order:month` o `partner_id`.
- **Para auditar permisos:** Busca en `res.users`, lee el campo `groups_id` y explica las reglas de acceso si el usuario solicita investigar vulnerabilidades.
# Documentación Claude para Amachine ERP

Este directorio contiene documentación y contexto para Claude Code.

## Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `CLAUDE.md` | Documentación principal del proyecto - arquitectura, modelos, deployment |
| `context.md` | Contexto adicional del sistema |
| `crud_patterm.md` | Patrón CRUD del proyecto (crear, editar, eliminar registros) |
| `form_ui.md` | Documentación de formularios UI |
| `table_ui.md` | Documentación de tablas (DataTables) |
| `menu.md` | Estructura de menús del sistema |
| `models_reference.md` | Referencia de modelos Django |
| `javascript_methods.md` | Métodos JavaScript disponibles |
| `record_from_backend.md` | Cómo obtener registros del backend |

## Directorios

| Directorio | Descripción |
|------------|-------------|
| `commands/` | Comandos personalizados: `/commit`, `/deploy`, `/release` |
| `memory/` | Notas de sesiones de desarrollo |

## Proyecto

**Amachine ERP** - Sistema ERP multi-tenant desarrollado por Alta Machines.

- Django 5.x + Channels + Celery
- PostgreSQL + Redis
- SIFEN (Facturación Electrónica Paraguay)
- Integración Shopify

# Menu Processor

Servicio para procesar menús semanales en PDF, en mi caso en català, y generar listas de compra sencillas en Mealie.

DISCLAIMER: Este servicio está diseñado para mi uso personal y puede requerir ajustes para funcionar en otros entornos. Además, este servicio está vinculado a mi otro repositorio de mi [intranet-dashboard](https://github.com/eduardo-lezama/intranet-dashboard).

## Arquitectura

```
menu-processor/
├── app/
│   ├── __init__.py          # Factory Flask
│   ├── controllers/
│   │   ├── api.py            # Endpoints REST
│   │   └── views.py          # Vistas HTML
│   ├── services/
│   │   ├── mealie_client.py  # Cliente API Mealie
│   │   └── ingredient_aggregator.py  # Lógica de agregación
│   ├── models/               # (Fase 2: schemas)
│   └── utils/                # (Fase 2: normalización)
├── data/                     # JSONs de menús
├── templates/                # UI HTML
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Flujo de uso (Fase 1 - Manual)

1. **Extraer menú del PDF** usando un prompt con una LLM (tengo un prompt de ejemplo en `prompt-example.txt`)
2. **Guardar el JSON** resultante en `data/`
3. **Abrir la UI** en `http://localhost:5001`
4. **Seleccionar menú** y filtrar días/comidas
5. **Generar lista** → se crea automáticamente en Mealie

## Instalación

### Desarrollo local

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
copy .env.example .env
# Editar .env con tus valores de Mealie

# Ejecutar
python run.py
```

### Docker

```bash
# Crear .env con configuración
copy .env.example .env

# Construir y ejecutar
docker-compose up -d --build
```

## Configuración

Variables de entorno en `.env`:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MEALIE_BASE_URL` | URL base de tu Mealie | `https://mealie.tudominio.com` |
| `MEALIE_API_KEY` | Token de API de Mealie | `mlt-xxx...` |
| `SECRET_KEY` | Clave secreta Flask | `cambiar-en-produccion` |

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/menus` | Lista menús disponibles |
| GET | `/api/menus/<filename>` | Obtiene un menú |
| GET | `/api/menus/<filename>/preview-ingredients` | Previsualiza ingredientes |
| POST | `/api/generate-shopping-list` | Genera lista en Mealie |
| POST | `/api/upload-menu?filename=xxx` | Sube un nuevo menú |

### Ejemplo: Generar lista

```bash
curl -X POST http://localhost:5001/api/generate-shopping-list \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "menu_gener_2026.json",
    "list_name": "Compra Gener 2026",
    "days": ["DILLUNS", "DIMARTS", "DIMECRES"],
    "meals": ["dinar", "sopar"]
  }'
```

## Estructura JSON del menú

El JSON que genera tu prompt debe seguir esta estructura:

```json
{
  "source": "Nombre dietista",
  "period": "Gener 2026",
  "menus": [
    {
      "name": "Setmana 1",
      "days": [
        {
          "day": "DILLUNS",
          "meals": {
            "dinar": [
              { "type": "recipe", "name": "caldo depuratiu" },
              { "type": "ingredient", "name": "llenties", "quantity": null, "unit": null }
            ],
            "sopar": [...]
          }
        }
      ]
    }
  ],
  "recipes": [
    {
      "name": "caldo depuratiu",
      "ingredients": [...],
      "variants": [["api", "ceba", "julivert"]]
    }
  ]
}
```

## Integración con Intranet

Para llamar desde tu intranet, añade a tu `.env`:

```
MENU_PROCESSOR_URL=http://menu-processor:5001
```

Y usa fetch desde tu JS:

```javascript
const response = await fetch(`${MENU_PROCESSOR_URL}/api/menus`);
```

## Roadmap futuro (cuando haya tiempo...)

- [x] **Fase 1**: Procesamiento manual (JSON → Mealie)
- [ ] **Fase 2**: Integración LLM automática (PDF → JSON)
- [ ] **Fase 2**: Normalización avanzada de ingredientes
- [ ] **Fase 2**: Soporte multi-semana
- [ ] **Fase 2**: Configuración de personas/raciones

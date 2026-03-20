"""
API endpoints para el procesador de menús
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from app.services.ingredient_aggregator import IngredientAggregator
from app.services.mealie_client import MealieClient

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {"status": "healthy", "timestamp": datetime.now().isoformat(), "service": "menu-processor"}
    )


@api_bp.route("/menus")
def list_menus():
    """Lista todos los archivos JSON de menús disponibles"""
    data_dir: Path = current_app.config["DATA_DIR"]
    menus = []

    for json_file in sorted(data_dir.glob("*.json")):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            menus.append(
                {
                    "filename": json_file.name,
                    "source": data.get("source", "Desconocido"),
                    "period": data.get("period", ""),
                    "num_menus": len(data.get("menus", [])),
                    "num_recipes": len(data.get("recipes", [])),
                }
            )
        except (OSError, json.JSONDecodeError) as e:
            current_app.logger.warning(f"Error leyendo {json_file}: {e}")

    return jsonify({"menus": menus})


@api_bp.route("/menus/<filename>")
def get_menu(filename):
    """Obtiene el contenido de un archivo de menú específico"""
    data_dir: Path = current_app.config["DATA_DIR"]
    file_path = data_dir / filename

    # Validación de seguridad
    if not file_path.suffix == ".json":
        return jsonify({"error": "Solo se permiten archivos .json"}), 400

    if not file_path.exists():
        return jsonify({"error": "Archivo no encontrado"}), 404

    try:
        # Verificar que está dentro de data_dir (prevenir path traversal)
        file_path.resolve().relative_to(data_dir.resolve())
    except ValueError:
        return jsonify({"error": "Acceso no permitido"}), 403

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400


@api_bp.route("/menus/<filename>/preview-ingredients")
def preview_ingredients(filename):
    """
    Previsualiza los ingredientes agregados de un menú sin crear la lista en Mealie.
    Útil para revisar antes de generar.
    """
    data_dir: Path = current_app.config["DATA_DIR"]
    file_path = data_dir / filename

    if not file_path.exists() or not file_path.suffix == ".json":
        return jsonify({"error": "Archivo no encontrado"}), 404

    try:
        with open(file_path, encoding="utf-8") as f:
            menu_data = json.load(f)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    # Opciones de filtrado
    days = request.args.getlist("days")  # ej: ?days=DILLUNS&days=DIMARTS
    meals = request.args.getlist("meals")  # ej: ?meals=dinar&meals=sopar

    aggregator = IngredientAggregator(menu_data)
    ingredients = aggregator.aggregate(
        filter_days=days if days else None, filter_meals=meals if meals else None
    )

    return jsonify(
        {
            "filename": filename,
            "filters": {"days": days, "meals": meals},
            "total_ingredients": len(ingredients),
            "ingredients": ingredients,
        }
    )


@api_bp.route("/generate-shopping-list", methods=["POST"])
def generate_shopping_list():
    """
    Genera una lista de compra en Mealie a partir de un menú.

    Body JSON:
    {
        "filename": "menu_gener_2026.json",
        "list_name": "Compra Gener 2026",  // opcional
        "days": ["DILLUNS", "DIMARTS"],    // opcional, filtra días
        "meals": ["dinar", "sopar"]        // opcional, filtra comidas
    }
    """
    data = request.get_json()

    if not data or "filename" not in data:
        return jsonify({"error": "Se requiere 'filename' en el body"}), 400

    filename = data["filename"]
    data_dir: Path = current_app.config["DATA_DIR"]
    file_path = data_dir / filename

    if not file_path.exists() or not file_path.suffix == ".json":
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Cargar menú
    try:
        with open(file_path, encoding="utf-8") as f:
            menu_data = json.load(f)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON inválido: {e}"}), 400

    # Agregar ingredientes
    aggregator = IngredientAggregator(menu_data)
    ingredients = aggregator.aggregate(filter_days=data.get("days"), filter_meals=data.get("meals"))

    if not ingredients:
        return jsonify({"error": "No se encontraron ingredientes"}), 400

    # Crear lista en Mealie
    mealie_url = current_app.config.get("MEALIE_BASE_URL")
    mealie_key = current_app.config.get("MEALIE_API_KEY")
    mealie_url_public = current_app.config.get("MEALIE_URL_PUBLIC") or mealie_url

    if not mealie_url or not mealie_key:
        return jsonify({"error": "Mealie no está configurado"}), 500

    try:
        client = MealieClient(mealie_url, mealie_key)

        # Nombre de la lista
        list_name = data.get("list_name") or f"Menú {menu_data.get('period', 'semanal')}"

        # Crear lista y añadir items
        shopping_list = client.create_shopping_list(list_name)
        list_id = shopping_list["id"]

        client.add_items_bulk(list_id, ingredients)

        return jsonify(
            {
                "success": True,
                "list_id": list_id,
                "list_name": list_name,
                "items_added": len(ingredients),
                "mealie_url": f"{mealie_url_public}/shopping-lists/{list_id}",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error creando lista en Mealie: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/upload-menu", methods=["POST"])
def upload_menu():
    """
    Sube un nuevo archivo JSON de menú.

    Body JSON: el contenido del menú directamente
    Query param: ?filename=menu_gener_2026.json
    """
    filename = request.args.get("filename")

    if not filename:
        return jsonify({"error": "Se requiere query param 'filename'"}), 400

    if not filename.endswith(".json"):
        filename += ".json"

    # Sanitizar nombre de archivo
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
    if not safe_filename:
        return jsonify({"error": "Nombre de archivo inválido"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON en el body"}), 400

    # Validación básica de estructura
    if "menus" not in data:
        return jsonify({"error": "El JSON debe contener 'menus'"}), 400

    data_dir: Path = current_app.config["DATA_DIR"]
    file_path = data_dir / safe_filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return jsonify({"success": True, "filename": safe_filename, "path": str(file_path)}), 201

    except OSError as e:
        return jsonify({"error": f"Error guardando archivo: {e}"}), 500

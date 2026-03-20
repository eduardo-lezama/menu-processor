"""
Servicio para agregar y deduplicar ingredientes de un menú
"""

from collections import defaultdict


class IngredientAggregator:
    """
    Procesa un menú JSON y extrae/agrega todos los ingredientes,
    expandiendo recetas y deduplicando.
    """

    def __init__(self, menu_data: dict):
        self.menu_data = menu_data
        self.recipes = self._index_recipes()

    def _index_recipes(self) -> dict:
        """Indexa las recetas por nombre para búsqueda rápida"""
        recipes = {}
        for recipe in self.menu_data.get("recipes", []):
            name = self._normalize_name(recipe.get("name", ""))
            if name:
                recipes[name] = recipe
        return recipes

    def _normalize_name(self, name: str) -> str:
        """Normaliza un nombre de ingrediente para comparación"""
        if not name:
            return ""
        # Minúsculas, quitar espacios extra
        return " ".join(name.lower().strip().split())

    def _parse_quantity(self, item: dict) -> tuple[str, float | None, str | None]:
        """
        Extrae nombre, cantidad y unidad de un item.

        Returns:
            (nombre, cantidad, unidad)
        """
        name = self._normalize_name(item.get("name", ""))
        quantity = item.get("quantity")
        unit = item.get("unit")

        # Intentar parsear cantidad si es string
        if isinstance(quantity, str):
            try:
                quantity = float(quantity.replace(",", "."))
            except ValueError:
                quantity = None

        return name, quantity, unit

    def _expand_recipe(self, recipe_name: str) -> list[str]:
        """
        Expande una receta a sus ingredientes.
        Si tiene variantes, usa la primera variante.
        """
        normalized = self._normalize_name(recipe_name)
        recipe = self.recipes.get(normalized)

        if not recipe:
            return []

        ingredients = []

        # Si tiene ingredientes directos
        if "ingredients" in recipe:
            for ing in recipe["ingredients"]:
                if isinstance(ing, dict):
                    name = ing.get("name", "")
                elif isinstance(ing, str):
                    name = ing
                else:
                    continue

                if name:
                    ingredients.append(self._normalize_name(name))

        # Si tiene variantes, usar la primera (o todas si queremos)
        if "variants" in recipe and recipe["variants"]:
            # Por ahora usamos la primera variante
            first_variant = recipe["variants"][0]
            for ing in first_variant:
                if isinstance(ing, str) and ing:
                    ingredients.append(self._normalize_name(ing))

        return ingredients

    def aggregate(
        self, filter_days: list[str] | None = None, filter_meals: list[str] | None = None
    ) -> list[str]:
        """
        Agrega todos los ingredientes del menú.

        Args:
            filter_days: Lista de días a incluir (ej: ["DILLUNS", "DIMARTS"])
            filter_meals: Lista de comidas a incluir (ej: ["dinar", "sopar"])

        Returns:
            Lista de ingredientes únicos y agregados
        """
        # Normalizar filtros
        if filter_days:
            filter_days = [d.upper() for d in filter_days]
        if filter_meals:
            filter_meals = [m.lower() for m in filter_meals]

        # Contador de ingredientes con cantidades
        ingredient_counts = defaultdict(lambda: {"count": 0, "quantities": []})

        # Procesar cada menú
        for menu in self.menu_data.get("menus", []):
            for day_data in menu.get("days", []):
                day_name = day_data.get("day", "").upper()

                # Filtrar por día
                if filter_days and day_name not in filter_days:
                    continue

                meals = day_data.get("meals", {})

                for meal_type, items in meals.items():
                    # Filtrar por tipo de comida
                    if filter_meals and meal_type.lower() not in filter_meals:
                        continue

                    for item in items:
                        item_type = item.get("type", "ingredient")

                        if item_type == "recipe":
                            # Expandir receta a ingredientes
                            recipe_name = item.get("name", "")
                            expanded = self._expand_recipe(recipe_name)

                            for ing_name in expanded:
                                if ing_name:
                                    ingredient_counts[ing_name]["count"] += 1

                        elif item_type == "ingredient":
                            name, quantity, unit = self._parse_quantity(item)

                            if name:
                                ingredient_counts[name]["count"] += 1
                                if quantity is not None:
                                    ingredient_counts[name]["quantities"].append((quantity, unit))

        # Formatear salida
        result = []
        for name, data in sorted(ingredient_counts.items()):
            if data["quantities"]:
                # Sumar cantidades del mismo tipo
                total = self._sum_quantities(data["quantities"])
                if total:
                    result.append(f"{total} {name}")
                else:
                    result.append(name)
            else:
                result.append(name)

        return result

    def _sum_quantities(self, quantities: list[tuple]) -> str | None:
        """
        Suma cantidades si tienen la misma unidad.

        Args:
            quantities: Lista de (cantidad, unidad)

        Returns:
            String formateado o None si no se puede sumar
        """
        if not quantities:
            return None

        # Agrupar por unidad
        by_unit = defaultdict(float)
        for qty, unit in quantities:
            if qty is not None:
                by_unit[unit or ""] += qty

        if not by_unit:
            return None

        # Si hay una sola unidad, formatear
        if len(by_unit) == 1:
            unit, total = list(by_unit.items())[0]
            if unit:
                return f"{total:.0f}{unit}" if total == int(total) else f"{total}{unit}"
            else:
                return f"{total:.0f}" if total == int(total) else str(total)

        # Si hay múltiples unidades, listar todas
        parts = []
        for unit, total in by_unit.items():
            formatted = f"{total:.0f}" if total == int(total) else str(total)
            if unit:
                parts.append(f"{formatted}{unit}")
            else:
                parts.append(formatted)

        return " + ".join(parts)

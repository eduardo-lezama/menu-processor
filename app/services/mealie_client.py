"""
Cliente para la API de Mealie - Gestión de listas de compra
"""

import requests


class MealieClient:
    """Cliente para interactuar con la API de Mealie"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def create_shopping_list(self, name: str) -> dict:
        """
        Crea una nueva lista de compra en Mealie.

        Args:
            name: Nombre de la lista

        Returns:
            dict con los datos de la lista creada (incluye 'id')
        """
        url = f"{self.base_url}/api/households/shopping/lists"

        response = self.session.post(url, json={"name": name}, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    def add_items_bulk(self, list_id: str, items: list[str]) -> dict:
        """
        Añade múltiples items a una lista de compra.

        Args:
            list_id: ID de la lista de compra
            items: Lista de strings con los nombres de los items

        Returns:
            dict con la respuesta de la API
        """
        url = f"{self.base_url}/api/households/shopping/items/create-bulk"

        payload = [{"shoppingListId": list_id, "note": item} for item in items]

        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    def get_shopping_lists(self) -> list:
        """
        Obtiene todas las listas de compra.

        Returns:
            Lista de listas de compra
        """
        url = f"{self.base_url}/api/households/shopping/lists"

        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        # Mealie puede devolver lista directa o paginada
        if isinstance(data, list):
            return data
        return data.get("items", [])

    def delete_shopping_list(self, list_id: str) -> bool:
        """
        Elimina una lista de compra.

        Args:
            list_id: ID de la lista a eliminar

        Returns:
            True si se eliminó correctamente
        """
        url = f"{self.base_url}/api/households/shopping/lists/{list_id}"

        response = self.session.delete(url, timeout=self.timeout)
        response.raise_for_status()

        return True

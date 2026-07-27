"""
user_profile.py
Gestor de persistencia para autollenado de datos del bolsista.
"""

import os
import json
from ui.config import PROJECT_DIR

PROFILE_FILE = os.path.join(PROJECT_DIR, "user_profile.json")


class UserProfile:
    """Guarda y carga los datos del bolsista para autollenado en los formularios."""

    @staticmethod
    def cargar() -> dict:
        """Carga el perfil guardado o retorna un diccionario vacío."""
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @staticmethod
    def guardar(datos: dict):
        """Guarda/actualiza los datos del perfil en el archivo JSON."""
        actual = UserProfile.cargar()
        # Actualizar con los campos no vacíos
        for k, v in datos.items():
            if v and isinstance(v, str):
                actual[k] = v.strip()
            elif v is not None and not isinstance(v, str):
                actual[k] = v
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(actual, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando perfil: {e}")

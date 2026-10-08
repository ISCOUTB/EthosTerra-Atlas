from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ActionValidationError(ValueError):
    pass


class ActionCatalogService:
    _catalog: dict[str, Any] | None = None
    _default_catalog_path: Path = Path(__file__).parent / "catalogs" / "actions_catalog_v1.json"
    _catalog_path: Path = _default_catalog_path

    @classmethod
    def set_catalog_path(cls, path: Path | str) -> None:
        """Permite configurar un catálogo de acciones variable o específico para un escenario de simulación."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Catálogo de acciones variable no encontrado en: {p}")
        cls._catalog_path = p
        cls._catalog = None  # Invalida caché para recarga inmediata

    @classmethod
    def reset_catalog(cls) -> None:
        """Restaura el catálogo por defecto de EthosTerra v1."""
        cls._catalog_path = cls._default_catalog_path
        cls._catalog = None

    @classmethod
    def get_catalog_path(cls) -> Path:
        return cls._catalog_path

    @classmethod
    def list_available_catalogs(cls) -> list[str]:
        """Lista los nombres de archivos de catálogo disponibles en el directorio oficial."""
        catalogs_dir = cls._default_catalog_path.parent
        if not catalogs_dir.is_dir():
            return []
        return sorted([f.name for f in catalogs_dir.glob("*.json")])

    @classmethod
    def load_catalog(cls) -> dict[str, Any]:
        if cls._catalog is None:
            if not cls._catalog_path.exists():
                raise FileNotFoundError(f"Catálogo de acciones no encontrado en: {cls._catalog_path}")
            with open(cls._catalog_path, "r", encoding="utf-8") as f:
                cls._catalog = json.load(f)
        return cls._catalog

    @classmethod
    def format_catalog_summary_for_prompt(cls) -> str:
        """Genera dinámicamente el resumen de acciones y operaciones permitidas para el prompt Zero-Trust."""
        cat = cls.load_catalog()
        version = cat.get("catalog_version", "1.0.0")
        actions = cat.get("actions", {})

        lines = [f"CATÁLOGO DE ACCIONES VÁLIDAS DE ETHOSTERRA (Versión activa: {version}):"]
        for action_name, spec in actions.items():
            arg_specs = spec.get("arg_specs", {})
            sub_ops = []
            for arg_name, aspec in arg_specs.items():
                allowed = aspec.get("allowed_values")
                if allowed:
                    sub_ops.append(f"{arg_name}: {allowed}")
            if sub_ops:
                lines.append(f"- '{action_name}' ({', '.join(sub_ops)})")
            else:
                lines.append(f"- '{action_name}'")
        return "\n".join(lines)

    @classmethod
    def get_actions(cls) -> dict[str, Any]:
        cat = cls.load_catalog()
        return cat.get("actions", {})

    @classmethod
    def get_action_count(cls) -> int:
        return len(cls.get_actions())

    @classmethod
    def validate_step(cls, action_name: str, args: dict[str, Any]) -> tuple[bool, list[str]]:
        errors: list[str] = []
        actions = cls.get_actions()

        if action_name not in actions:
            return False, [f"Acción '{action_name}' no existe en el catálogo de EthosTerra."]

        spec = actions[action_name]
        required_args = spec.get("required_args", [])
        allow_extra = spec.get("allow_extra_args", False)
        arg_specs = spec.get("arg_specs", {})

        # 1. Comprobar argumentos obligatorios
        for req in required_args:
            if req not in args:
                errors.append(f"Acción '{action_name}' requiere el argumento obligatorio '{req}'.")

        # 2. Comprobar argumentos extra
        if not allow_extra:
            allowed_keys = set(required_args) | set(spec.get("optional_args", []))
            for key in args:
                if key not in allowed_keys:
                    errors.append(f"Acción '{action_name}' no permite el argumento no reconocido '{key}'.")

        # 3. Validar valores permitidos y tipos básicos
        for key, val in args.items():
            if key in arg_specs:
                aspec = arg_specs[key]
                allowed_vals = aspec.get("allowed_values")
                if allowed_vals is not None and val not in allowed_vals:
                    errors.append(
                        f"Argumento '{key}' con valor '{val}' no es válido para '{action_name}'. "
                        f"Valores permitidos: {allowed_vals}."
                    )
                atype = aspec.get("type")
                if atype == "string" and not isinstance(val, str):
                    errors.append(f"Argumento '{key}' debe ser string, se recibió {type(val).__name__}.")
                elif atype == "number" and not isinstance(val, (int, float)):
                    errors.append(f"Argumento '{key}' debe ser numérico, se recibió {type(val).__name__}.")
                elif atype == "integer" and not isinstance(val, int):
                    errors.append(f"Argumento '{key}' debe ser entero, se recibió {type(val).__name__}.")

        return len(errors) == 0, errors

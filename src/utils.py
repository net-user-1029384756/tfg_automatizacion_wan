"""
Utilidades comunes: configuración de logging y carga del inventario YAML.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Type

import yaml

from .models import CiscoDevice, MikroTikDevice, NetworkDevice

DEVICE_TYPES: Dict[str, Type[NetworkDevice]] = {
    "mikrotik": MikroTikDevice,
    "cisco": CiscoDevice,
}


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configura el logging del paquete con un formato uniforme.

    :param level: Nivel de logging (``logging.INFO``, ``logging.DEBUG``...).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _resolve_secret(value: str) -> str:
    """
    Si ``value`` empieza por ``env:``, devuelve la variable de entorno.

    Esto evita almacenar contraseñas en texto plano en el YAML.
    """
    if value.startswith("env:"):
        var_name = value.split(":", 1)[1]
        secret = os.environ.get(var_name)
        if secret is None:
            raise ValueError(
                f"Variable de entorno '{var_name}' no definida; "
                f"revisa tu fichero .env"
            )
        return secret
    return value


def load_inventory(path: str | Path) -> List[NetworkDevice]:
    """
    Carga un inventario YAML y devuelve instancias de dispositivo.

    Estructura esperada del YAML::

        devices:
          - hostname: R1
            type: mikrotik
            ip_address: 192.168.99.10
            username: admin
            password: env:TFG_MIKROTIK_PASS

    :param path: Ruta al fichero YAML.
    :return: Lista de ``NetworkDevice``.
    :raises FileNotFoundError: Si el fichero no existe.
    :raises ValueError: Si un dispositivo declara un tipo desconocido.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Inventario no encontrado: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    devices: List[NetworkDevice] = []
    for entry in data.get("devices", []):
        device_type = entry.get("type", "").lower()
        device_cls = DEVICE_TYPES.get(device_type)
        if device_cls is None:
            raise ValueError(
                f"Tipo de dispositivo desconocido: '{device_type}'. "
                f"Válidos: {sorted(DEVICE_TYPES)}"
            )
        devices.append(
            device_cls(
                hostname=entry["hostname"],
                ip_address=entry["ip_address"],
                username=_resolve_secret(entry["username"]),
                password=_resolve_secret(entry["password"]),
            )
        )
    return devices

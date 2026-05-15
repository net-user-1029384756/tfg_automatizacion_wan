"""
Fase 1 — Preparación offline del inventario Day 0.

Lee devices.yml y mac_map.yml, genera una contraseña segura por router,
la guarda en .env y actualiza devices.yml para que cada entrada apunte a
su propia variable de entorno (env:R1_PASS, env:R2_PASS, ...).

No requiere conexión a los routers. Ejecutar ANTES de provisioning.py.

Uso:
    python -m src.prep_inventory
    python -m src.prep_inventory --inventory inventory/devices.yml \\
                                 --mac-map inventory/mac_map.yml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

import yaml
from dotenv import load_dotenv

from .utils import (
    configure_logging,
    generate_secure_password,
    load_mac_map,
    update_env_file,
)

logger = logging.getLogger(__name__)


def prep_inventory(
    inventory_path: Path,
    mac_map_path: Path,
    env_path: Path = Path(".env"),
) -> None:
    """
    Genera contraseñas por router, actualiza .env y devices.yml.

    :param inventory_path: Ruta a devices.yml.
    :param mac_map_path: Ruta a mac_map.yml (usada para validación).
    :param env_path: Ruta al fichero .env donde se guardan las contraseñas.
    """
    mac_map = load_mac_map(mac_map_path)
    known_hostnames = set(mac_map.values())

    with inventory_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    devices = data.get("devices", [])
    if not devices:
        logger.warning("No hay dispositivos en %s.", inventory_path)
        return

    for entry in devices:
        hostname = entry.get("hostname", "")

        if hostname not in known_hostnames:
            logger.warning(
                "Hostname '%s' no tiene MAC en mac_map.yml; "
                "la identificación automática fallará en la Fase 2.",
                hostname,
            )

        env_key = f"{hostname}_PASS"
        password = generate_secure_password()

        update_env_file(env_key, password, env_path)
        entry["password"] = f"env:{env_key}"

        logger.info("%-4s → %s generada y guardada en .env", hostname, env_key)

    with inventory_path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, allow_unicode=True)

    logger.info("devices.yml actualizado: %s", inventory_path)
    logger.info("Fase 1 completada. Ejecuta ahora: python -m src.provisioning")


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="prep",
        description="Fase 1: preparación offline del inventario Day 0.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("inventory/devices.yml"),
        metavar="PATH",
        help="Inventario de dispositivos (por defecto: inventory/devices.yml).",
    )
    parser.add_argument(
        "--mac-map",
        type=Path,
        default=Path("inventory/mac_map.yml"),
        metavar="PATH",
        help="Mapa MAC→hostname (por defecto: inventory/mac_map.yml).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        metavar="PATH",
        help="Fichero .env donde guardar las contraseñas (por defecto: .env).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Activa logging en nivel DEBUG.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    load_dotenv()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    for path in (args.inventory, args.mac_map):
        if not path.is_file():
            logger.error("Fichero no encontrado: %s", path)
            return 1

    prep_inventory(args.inventory, args.mac_map, args.env_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())

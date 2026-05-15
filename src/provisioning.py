"""
Fase 2 — Provisionamiento online Day 0.

REQUIERE haber ejecutado prep_inventory.py antes (Fase 1).

Conecta a cada router con las credenciales de fábrica (admin / vacía),
gestiona el prompt de primer arranque de ROS7, identifica el router por
la MAC de ether1 y aplica la contraseña objetivo que preparó la Fase 1.

Uso:
    # Lee IPs del inventario automáticamente
    python -m src.provisioning

    # IPs explícitas
    python -m src.provisioning 192.168.233.130 192.168.233.131 ...
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv

from .connector import DeviceConnectionError, DeviceConnector
from .models import MikroTikDevice
from .utils import configure_logging, load_mac_map

logger = logging.getLogger(__name__)

_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = ""


def _ips_from_inventory(path: Path) -> List[str]:
    """Lee las IPs del inventario YAML sin resolver secretos."""
    if not path.is_file():
        raise FileNotFoundError(f"Inventario no encontrado: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return [entry["ip_address"] for entry in data.get("devices", [])]


def provision_device(ip_address: str, mac_map: Dict[str, str]) -> bool:
    """
    Provisiona un único router MikroTik (Fase 2).

    Conecta con credenciales de fábrica, identifica el router por MAC,
    y aplica la contraseña objetivo generada por la Fase 1.

    :param ip_address: IP de gestión del router.
    :param mac_map: Diccionario {MAC: hostname}.
    :return: True si el provisionamiento tuvo éxito.
    """
    device = MikroTikDevice(
        hostname=ip_address,
        ip_address=ip_address,
        username=_DEFAULT_USERNAME,
        password=_DEFAULT_PASSWORD,
    )

    try:
        with DeviceConnector(device) as conn:
            # 1. Identificar por MAC de ether1
            mac = device.get_management_mac(conn)
            logger.info("[%s] MAC ether1: %s", ip_address, mac)

            hostname = mac_map.get(mac.upper())
            if hostname is None:
                logger.warning(
                    "[%s] MAC %s no encontrada en mac_map; dispositivo omitido.",
                    ip_address,
                    mac,
                )
                return False

            logger.info("[%s] Identificado como: %s", ip_address, hostname)

            # 2. Leer contraseña objetivo preparada por la Fase 1
            env_key = f"{hostname}_PASS"
            target_password = os.environ.get(env_key)
            if not target_password:
                logger.error(
                    "[%s] Variable %s no encontrada en el entorno. "
                    "¿Ejecutaste prep_inventory.py primero?",
                    ip_address,
                    env_key,
                )
                return False

            # 3. Aplicar contraseña objetivo (entrecomillada para ROS7)
            conn.configure([f'/user set admin password="{target_password}"'])
            logger.info("[%s] Contraseña aplicada desde %s.", ip_address, env_key)

            # 4. Cambiar identidad y actualizar el prompt de Netmiko inmediatamente,
            #    evitando timeout por cambio de hostname en el canal SSH.
            conn.configure([f"/system identity set name={hostname}"])
            conn._connection.set_base_prompt()
            logger.info("[%s] Identidad asignada: %s", ip_address, hostname)

    except DeviceConnectionError as exc:
        logger.error("[%s] Error de conexión: %s", ip_address, exc)
        return False
    except ValueError as exc:
        logger.error("[%s] No se pudo identificar el dispositivo: %s", ip_address, exc)
        return False

    return True


def run_provisioning(ips: List[str], mac_map: Dict[str, str]) -> int:
    """Provisiona cada IP y devuelve el número de fallos."""
    failed = 0
    for ip in ips:
        logger.info("--- Provisionando %s ---", ip)
        if not provision_device(ip, mac_map):
            failed += 1
    return failed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="provision",
        description="Fase 2: provisionamiento online Day 0 de routers MikroTik.",
    )
    parser.add_argument(
        "--mac-map",
        type=Path,
        default=Path("inventory/mac_map.yml"),
        metavar="PATH",
        help="Ruta al fichero mac_map.yml (por defecto: inventory/mac_map.yml).",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("inventory/devices.yml"),
        metavar="PATH",
        help="Inventario del que leer IPs si no se pasan como argumento.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logging en nivel DEBUG.",
    )
    parser.add_argument(
        "ips",
        nargs="*",
        metavar="IP",
        help="IPs a provisionar. Si se omite, se leen de --inventory.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    load_dotenv()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        mac_map = load_mac_map(args.mac_map)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    ips = args.ips
    if not ips:
        try:
            ips = _ips_from_inventory(args.inventory)
            logger.info("IPs leídas del inventario: %s", ", ".join(ips))
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            return 1

    if not ips:
        logger.error("No hay IPs que provisionar.")
        return 1

    logger.info("Iniciando Fase 2 para %d dispositivo(s).", len(ips))
    return run_provisioning(ips, mac_map)


if __name__ == "__main__":
    sys.exit(main())

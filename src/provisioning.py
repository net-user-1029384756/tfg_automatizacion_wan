"""
Provisionamiento Day 0 de routers MikroTik.

Conecta con credenciales por defecto (admin / sin contraseña), identifica
cada router por la MAC de ether1, asigna su nombre y establece una contraseña
segura generada aleatoriamente. Guarda las nuevas credenciales en el .env.

Uso:
    python -m src.provisioning 192.168.233.130 192.168.233.131 ...
    python -m src.provisioning --mac-map inventory/mac_map.yml <IPs>
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv

from .connector import DeviceConnectionError, DeviceConnector
from .models import MikroTikDevice
from .utils import configure_logging, generate_secure_password, update_env_file

logger = logging.getLogger(__name__)

_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = ""


def load_mac_map(path: str | Path) -> Dict[str, str]:
    """Carga el fichero mac_map.yml y devuelve {MAC_UPPER: hostname}."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Mapa de MACs no encontrado: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return {mac.upper(): hostname for mac, hostname in data.get("mac_map", {}).items()}


def provision_device(ip_address: str, mac_map: Dict[str, str]) -> bool:
    """
    Provisiona un único router.

    :param ip_address: IP de gestión del router.
    :param mac_map: Diccionario {MAC: hostname}.
    :return: True si el provisionamiento tuvo éxito.
    """
    temp_device = MikroTikDevice(
        hostname=ip_address,
        ip_address=ip_address,
        username=_DEFAULT_USERNAME,
        password=_DEFAULT_PASSWORD,
    )

    try:
        with DeviceConnector(temp_device) as conn:
            # 1. Identificar por MAC de ether1
            mac = temp_device.get_management_mac(conn)
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

            # 2. Asignar nombre al router
            conn.configure([f"/system identity set name={hostname}"])
            logger.info("[%s] Identidad asignada: %s", ip_address, hostname)

            # 3. Generar nueva contraseña y aplicarla
            new_password = generate_secure_password()
            conn.configure([f"/user set [find name=admin] password={new_password}"])
            logger.info("[%s] Contraseña actualizada en el dispositivo.", ip_address)

            # 4. Persistir en .env
            env_key = f"TFG_{hostname}_PASS"
            update_env_file(env_key, new_password)
            logger.info("[%s] .env actualizado → %s", ip_address, env_key)

    except DeviceConnectionError as exc:
        logger.error("[%s] Error de conexión con credenciales por defecto: %s", ip_address, exc)
        return False
    except ValueError as exc:
        logger.error("[%s] No se pudo identificar el dispositivo: %s", ip_address, exc)
        return False

    return True


def run_provisioning(ips: List[str], mac_map: Dict[str, str]) -> int:
    """Provisiona cada IP de la lista y devuelve el número de fallos."""
    failed = 0
    for ip in ips:
        logger.info("--- Provisionando %s ---", ip)
        if not provision_device(ip, mac_map):
            failed += 1
    return failed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tfg-provision",
        description="Provisionamiento Day 0 de routers MikroTik.",
    )
    parser.add_argument(
        "--mac-map",
        type=Path,
        default=Path("inventory/mac_map.yml"),
        metavar="PATH",
        help="Ruta al fichero mac_map.yml (por defecto: inventory/mac_map.yml).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logging en nivel DEBUG.",
    )
    parser.add_argument(
        "ips",
        nargs="+",
        metavar="IP",
        help="Direcciones IP de los routers a provisionar.",
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

    logger.info(
        "Iniciando provisionamiento Day 0 para %d dispositivo(s).", len(args.ips)
    )
    return run_provisioning(args.ips, mac_map)


if __name__ == "__main__":
    sys.exit(main())

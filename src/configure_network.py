"""
Fase 4 — Configuración de la Red de Datos.

Lee devices.yml y network_config.yml, conecta a cada router y:
  1. Habilita las interfaces definidas.
  2. Elimina IPs previas en cada interfaz (limpieza, evita duplicados).
  3. Aplica las IPs definidas en network_config.yml.

Uso:
    python -m src.configure_network
    python -m src.configure_network --network-config inventory/network_config.yml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

from .connector import DeviceConnectionError, DeviceConnector
from .utils import configure_logging, load_inventory

logger = logging.getLogger(__name__)


def load_network_config(path: Path) -> Dict[str, Any]:
    """Carga network_config.yml y devuelve el dict completo."""
    if not path.is_file():
        raise FileNotFoundError(f"Configuración de red no encontrada: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def configure_device(
    connector: DeviceConnector,
    hostname: str,
    interfaces: List[Dict[str, str]],
) -> None:
    """
    Configura las interfaces de un router.

    Por cada interfaz definida:
      1. La habilita si está desactivada.
      2. Elimina cualquier IP previa asignada a esa interfaz.
      3. Aplica la IP definida en network_config.yml.

    :param connector: Conector SSH activo.
    :param hostname: Nombre del router (para logging).
    :param interfaces: Lista de dicts con 'name', 'address' y 'description'.
    """
    for iface in interfaces:
        name = iface["name"]
        address = iface["address"]
        description = iface.get("description", "")

        # 1. Habilitar interfaz
        logger.info("[%s] Habilitando %s...", hostname, name)
        connector.run(f"/interface enable {name}")

        # 2. Limpiar IPs previas en esta interfaz para evitar duplicados
        logger.info("[%s] Eliminando IPs previas en %s...", hostname, name)
        output = connector.run(f"/ip address remove [find interface={name}]")
        if output.strip():
            logger.debug("[%s] Salida de remove en %s: %s", hostname, name, output.strip())

        # 3. Aplicar nueva IP
        logger.info("[%s] %s → %s  (%s)", hostname, name, address, description)
        connector.run(f"/ip address add address={address} interface={name}")

    logger.info("[%s] Configuración de interfaces completada.", hostname)


def run_network_config(
    inventory_path: Path,
    network_config_path: Path,
) -> int:
    """
    Carga inventario y config de red, conecta y configura cada router.

    :return: Número de routers con error.
    """
    devices = load_inventory(inventory_path)
    net_cfg = load_network_config(network_config_path)
    router_configs = net_cfg.get("routers", {})

    failed = 0
    for device in devices:
        hostname = device.hostname

        if hostname not in router_configs:
            logger.warning(
                "[%s] Sin entrada en network_config.yml; omitido.", hostname
            )
            continue

        interfaces = router_configs[hostname].get("interfaces", [])
        if not interfaces:
            logger.warning("[%s] Sin interfaces definidas; omitido.", hostname)
            continue

        logger.info("--- Configurando %s (%s) ---", hostname, device.ip_address)
        try:
            with DeviceConnector(device) as conn:
                configure_device(conn, hostname, interfaces)
        except DeviceConnectionError as exc:
            logger.error("[%s] Error de conexión: %s", hostname, exc)
            failed += 1

    return failed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="configure-network",
        description="Fase 4: configuración de IPs en los routers.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("inventory/devices.yml"),
        metavar="PATH",
        help="Inventario de dispositivos (por defecto: inventory/devices.yml).",
    )
    parser.add_argument(
        "--network-config",
        type=Path,
        default=Path("inventory/network_config.yml"),
        metavar="PATH",
        help="Configuración de red (por defecto: inventory/network_config.yml).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logging en nivel DEBUG.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    load_dotenv()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    for path in (args.inventory, args.network_config):
        if not path.is_file():
            logger.error("Fichero no encontrado: %s", path)
            return 1

    logger.info("Iniciando Fase 4: configuración de red de datos.")
    failed = run_network_config(args.inventory, args.network_config)

    if failed:
        logger.warning("Fase 4 completada con %d error(es).", failed)
    else:
        logger.info("Fase 4 completada sin errores.")

    return failed


if __name__ == "__main__":
    sys.exit(main())

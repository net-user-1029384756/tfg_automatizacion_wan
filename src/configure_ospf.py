"""
Fase 5 — Configuración de OSPFv2 (MikroTik RouterOS 7).

Lee devices.yml y network_config.yml, conecta a cada router y aplica
la configuración OSPF en tres pasos idempotentes:

  A. Limpieza de cualquier configuración OSPF previa.
  B. Creación de la instancia OSPF y el área backbone (0.0.0.0).
  C. Registro de cada interfaz de datos en la plantilla OSPF.

Uso:
    python -m src.configure_ospf
    python -m src.configure_ospf --network-config inventory/network_config.yml
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


def configure_ospf_device(
    connector: DeviceConnector,
    hostname: str,
    interfaces: List[Dict[str, str]],
) -> None:
    logger.info("[%s] Preparando configuración OSPFv2...", hostname)
    commands = [
        "/routing ospf interface-template remove [find]",
        "/routing ospf area remove [find]",
        "/routing ospf instance remove [find]",
        "/routing ospf instance add name=default-v2",
        "/routing ospf area add instance=default-v2 name=backbone area-id=0.0.0.0",
    ]
    for iface in interfaces:
        commands.append(
            f"/routing ospf interface-template add area=backbone interfaces={iface['name']}"
        )

    logger.info("[%s] Aplicando %d líneas de configuración OSPF en bloque...", hostname, len(commands))
    connector.configure(commands)
    logger.info("[%s] Configuración OSPF completada con éxito.", hostname)


def run_ospf_config(
    inventory_path: Path,
    network_config_path: Path,
) -> int:
    """
    Carga inventario y config de red, conecta y configura OSPF en cada router.

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

        logger.info("--- Configurando OSPF en %s (%s) ---", hostname, device.ip_address)
        try:
            with DeviceConnector(device) as conn:
                configure_ospf_device(conn, hostname, interfaces)
        except DeviceConnectionError as exc:
            logger.error("[%s] Error de conexión: %s", hostname, exc)
            failed += 1

    return failed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="configure-ospf",
        description="Fase 5: configuración de OSPFv2 en los routers.",
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

    logger.info("Iniciando Fase 5: configuración de OSPFv2.")
    failed = run_ospf_config(args.inventory, args.network_config)

    if failed:
        logger.warning("Fase 5 completada con %d error(es).", failed)
    else:
        logger.info("Fase 5 completada sin errores.")

    return failed


if __name__ == "__main__":
    sys.exit(main())

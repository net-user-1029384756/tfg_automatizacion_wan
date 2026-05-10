"""
Punto de entrada del proyecto.

Lee el inventario YAML, abre una sesión SSH contra cada dispositivo y ejecuta
un comando de identificación. Funciona como *smoke test* de la iteración
inicial: si Python puede listar la identidad de los routers, el resto del
proyecto puede apoyarse en este conector.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from .connector import DeviceConnectionError, DeviceConnector
from .models import CiscoDevice, MikroTikDevice, NetworkDevice
from .utils import configure_logging, load_inventory

logger = logging.getLogger(__name__)

IDENTITY_COMMANDS = {
    MikroTikDevice: "/system identity print",
    CiscoDevice: "show version | include uptime",
}


def _identity_command(device: NetworkDevice) -> str:
    """Devuelve el comando de identidad apropiado para el tipo de dispositivo."""
    return IDENTITY_COMMANDS.get(type(device), "")


def ping_devices(devices: List[NetworkDevice]) -> int:
    """
    Conecta y ejecuta el comando de identidad en cada dispositivo.

    :param devices: Lista de dispositivos a sondear.
    :return: Número de dispositivos que han fallado.
    """
    failed = 0
    for device in devices:
        command = _identity_command(device)
        if not command:
            logger.warning(
                "Sin comando de identidad para %s (tipo %s); se omite.",
                device.hostname,
                type(device).__name__,
            )
            continue
        try:
            with DeviceConnector(device) as conn:
                output = conn.run(command)
                logger.info("[%s] %s", device.hostname, output.strip())
        except DeviceConnectionError as exc:
            logger.error("[%s] %s", device.hostname, exc)
            failed += 1
    return failed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Define y procesa los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="tfg-wan",
        description="Automatización de la configuración de routers/switches.",
    )
    parser.add_argument(
        "-i",
        "--inventory",
        type=Path,
        default=Path("inventory/devices.yml"),
        help="Ruta al inventario YAML (por defecto: inventory/devices.yml).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logging en nivel DEBUG.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """
    Función principal.

    :return: Código de salida (0 OK, >0 número de dispositivos con error).
    """
    args = _parse_args(argv)
    load_dotenv()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        devices = load_inventory(args.inventory)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("No se pudo cargar el inventario: %s", exc)
        return 1

    if not devices:
        logger.warning("El inventario está vacío.")
        return 0

    logger.info("Sondeando %d dispositivos...", len(devices))
    return ping_devices(devices)


if __name__ == "__main__":
    sys.exit(main())

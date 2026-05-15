"""
Fase de Validación — Verificación de conectividad y convergencia OSPF.

Para cada router del inventario, ejecuta un ping a cada red LAN objetivo
y analiza la salida de MikroTik para determinar si el ping fue exitoso.
Al final imprime un resumen con el total de pruebas pasadas/fallidas.

Uso:
    python -m src.verify_network
    python -m src.verify_network --verbose
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

# IPs LAN objetivo a verificar desde cada router
TARGETS: List[str] = ["192.168.3.1", "192.168.4.1"]


def load_network_config(path: Path) -> Dict[str, Any]:
    """Carga network_config.yml y devuelve el dict completo."""
    if not path.is_file():
        raise FileNotFoundError(f"Configuración de red no encontrada: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_router_local_ips(router_cfg: Dict[str, Any]) -> set[str]:
    """Devuelve el conjunto de IPs (sin prefijo) configuradas en el router."""
    ips: set[str] = set()
    for iface in router_cfg.get("interfaces", []):
        addr = iface.get("address", "")
        ips.add(addr.split("/")[0])
    return ips


def ping_target(connector: DeviceConnector, hostname: str, target: str) -> bool:
    """
    Ejecuta /ping a target con count=3 y devuelve True si packet-loss=0%.

    :param connector: Conector SSH activo.
    :param hostname: Nombre del router (para logging).
    :param target: IP destino del ping.
    :return: True si el ping fue exitoso.
    """
    logger.debug("[%s] Ejecutando ping a %s...", hostname, target)
    output = connector.run(f"/ping address={target} count=3", )
    logger.debug("[%s] Salida ping %s: %s", hostname, target, output.strip())

    if "packet-loss=0%" in output:
        return True
    return False


def verify_device(
    connector: DeviceConnector,
    hostname: str,
    local_ips: set[str],
    targets: List[str],
    results: List[Dict[str, str]],
) -> None:
    """
    Ejecuta todos los pings para un router y acumula resultados.

    :param connector: Conector SSH activo.
    :param hostname: Nombre del router.
    :param local_ips: IPs propias del router (para detectar pruebas locales).
    :param targets: Lista de IPs a verificar.
    :param results: Lista compartida donde se añaden los resultados.
    """
    for target in targets:
        if target in local_ips:
            logger.info("[%s] → %s  : LOCAL (omitido)", hostname, target)
            results.append({"router": hostname, "target": target, "status": "LOCAL"})
            continue

        try:
            success = ping_target(connector, hostname, target)
        except Exception as exc:
            logger.warning("[%s] → %s  : ERROR durante ping (%s)", hostname, target, exc)
            results.append({"router": hostname, "target": target, "status": "ERROR"})
            continue

        if success:
            logger.info("[%s] → %s  : OK", hostname, target)
            results.append({"router": hostname, "target": target, "status": "OK"})
        else:
            logger.warning("[%s] → %s  : FALLO (packet-loss > 0%%)", hostname, target)
            results.append({"router": hostname, "target": target, "status": "FALLO"})


def print_summary(results: List[Dict[str, str]]) -> int:
    """
    Imprime el resumen de resultados y devuelve el número de fallos.

    :return: Número de pruebas fallidas (excluye LOCAL).
    """
    executed = [r for r in results if r["status"] != "LOCAL"]
    passed = [r for r in executed if r["status"] == "OK"]
    failed = [r for r in executed if r["status"] != "OK"]

    logger.info("")
    logger.info("=" * 50)
    logger.info("  RESUMEN DE VALIDACIÓN")
    logger.info("=" * 50)
    for r in results:
        status = r["status"]
        marker = "✓" if status == "OK" else ("~" if status == "LOCAL" else "✗")
        logger.info("  %s  [%s] → %s  : %s", marker, r["router"], r["target"], status)
    logger.info("-" * 50)
    logger.info(
        "  TOTAL: %d/%d pruebas exitosas",
        len(passed),
        len(executed),
    )
    logger.info("=" * 50)

    return len(failed)


def run_verification(
    inventory_path: Path,
    network_config_path: Path,
    targets: List[str],
) -> int:
    """
    Conecta a cada router, ejecuta los pings y muestra el resumen.

    :return: Número de pruebas fallidas.
    """
    devices = load_inventory(inventory_path)
    net_cfg = load_network_config(network_config_path)
    router_configs = net_cfg.get("routers", {})

    results: List[Dict[str, str]] = []

    for device in devices:
        hostname = device.hostname
        local_ips = get_router_local_ips(router_configs.get(hostname, {}))

        logger.info("--- Verificando %s (%s) ---", hostname, device.ip_address)
        try:
            with DeviceConnector(device) as conn:
                verify_device(conn, hostname, local_ips, targets, results)
        except DeviceConnectionError as exc:
            logger.error("[%s] Error de conexión: %s", hostname, exc)
            for target in targets:
                results.append({"router": hostname, "target": target, "status": "ERROR"})

    return print_summary(results)


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify-network",
        description="Fase de Validación: verifica conectividad y convergencia OSPF.",
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
        help="Configuración de red para detectar IPs locales (por defecto: inventory/network_config.yml).",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=TARGETS,
        metavar="IP",
        help=f"IPs a verificar (por defecto: {' '.join(TARGETS)}).",
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

    logger.info("Iniciando verificación de red. Targets: %s", ", ".join(args.targets))
    return run_verification(args.inventory, args.network_config, args.targets)


if __name__ == "__main__":
    sys.exit(main())

"""
Módulo de conexión SSH a dispositivos de red.

Provee :class:`DeviceConnector`, un envoltorio sobre Netmiko que se usa como
gestor de contexto (``with``) para garantizar el cierre de la sesión incluso
si se produce un error durante la ejecución de comandos.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

from .models import NetworkDevice

logger = logging.getLogger(__name__)


class DeviceConnectionError(Exception):
    """Error genérico al conectar o ejecutar comandos contra un dispositivo."""


class DeviceConnector:
    """
    Envuelve una conexión Netmiko como gestor de contexto.

    Ejemplo de uso::

        device = MikroTikDevice("R1", "192.168.99.10", "admin", "***")
        with DeviceConnector(device) as conn:
            print(conn.run("/system identity print"))
    """

    def __init__(self, device: NetworkDevice, read_timeout: int = 15) -> None:
        """
        Inicializa el conector.

        :param device: Instancia de ``NetworkDevice`` (o subclase).
        :param read_timeout: Tiempo máximo de lectura por comando en segundos.
        """
        self.device = device
        self.read_timeout = read_timeout
        self._connection = None  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DeviceConnector":
        """Abre la sesión SSH al entrar en el bloque ``with``."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cierra la sesión al salir del bloque, incluso ante excepciones."""
        self.disconnect()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Establece la conexión SSH usando los parámetros del dispositivo."""
        params = self.device.get_connection_config()
        logger.info(
            "Conectando a %s (%s) como %s",
            self.device.hostname,
            self.device.ip_address,
            self.device.username,
        )
        try:
            self._connection = ConnectHandler(**params)
        except NetmikoAuthenticationException as exc:
            raise DeviceConnectionError(
                f"Fallo de autenticación contra {self.device.hostname}"
            ) from exc
        except NetmikoTimeoutException as exc:
            raise DeviceConnectionError(
                f"Timeout al conectar con {self.device.hostname} "
                f"({self.device.ip_address})"
            ) from exc

    def disconnect(self) -> None:
        """Cierra la conexión SSH si está abierta."""
        if self._connection is not None:
            logger.info("Cerrando sesión con %s", self.device.hostname)
            self._connection.disconnect()
            self._connection = None

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------

    def run(self, command: str) -> str:
        """
        Ejecuta un comando en modo no privilegiado y devuelve la salida.

        :param command: Comando a ejecutar (sintaxis del dispositivo).
        :return: Salida del comando como texto.
        :raises DeviceConnectionError: Si no hay sesión activa.
        """
        if self._connection is None:
            raise DeviceConnectionError(
                "No hay conexión activa; usa el conector dentro de un 'with'."
            )
        logger.debug("[%s] $ %s", self.device.hostname, command)
        return self._connection.send_command(
            command, read_timeout=self.read_timeout
        )

    def configure(self, commands: List[str]) -> str:
        """
        Aplica una lista de comandos de configuración.

        :param commands: Lista de líneas de configuración.
        :return: Salida combinada de la operación.
        """
        if self._connection is None:
            raise DeviceConnectionError(
                "No hay conexión activa; usa el conector dentro de un 'with'."
            )
        logger.info(
            "[%s] aplicando %d líneas de configuración",
            self.device.hostname,
            len(commands),
        )
        return self._connection.send_config_set(commands)

    @property
    def is_connected(self) -> bool:
        """Indica si la sesión está abierta."""
        return self._connection is not None

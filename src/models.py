"""
Módulo de modelos para la automatización de infraestructura de red.
Define la jerarquía de clases para dispositivos MikroTik y Cisco.
"""

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .connector import DeviceConnector

class NetworkDevice(ABC):
    """Clase base abstracta para cualquier dispositivo de red."""

    def __init__(self, hostname: str, ip_address: str, username: str, password: str):
        """
        Inicializa un dispositivo de red.

        :param hostname: Nombre del dispositivo.
        :param ip_address: Dirección IP de gestión.
        :param username: Usuario para la conexión SSH.
        :param password: Contraseña para la conexión SSH.
        """
        self.hostname = hostname
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.connection_params: Dict[str, Any] = {
            "host": self.ip_address,
            "username": self.username,
            "password": self.password,
            "port": 22,
        }

    @abstractmethod
    def get_connection_config(self) -> Dict[str, Any]:
        """Devuelve los parámetros de conexión específicos para Netmiko."""
        pass

class MikroTikDevice(NetworkDevice):
    """Representa un dispositivo MikroTik RouterOS."""

    def get_connection_config(self) -> Dict[str, Any]:
        """Retorna la configuración de conexión para MikroTik."""
        config = self.connection_params.copy()
        config["device_type"] = "mikrotik_routeros"
        return config

    def get_management_mac(self, connection: "DeviceConnector") -> str:
        """Devuelve la MAC de ether1 ejecutando /interface/ethernet/print."""
        output = connection.run("/interface/ethernet/print")
        mac_pattern = re.compile(
            r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})"
        )
        for line in output.splitlines():
            if re.search(r"\bether1\b", line):
                match = mac_pattern.search(line)
                if match:
                    return match.group(1).upper()
        raise ValueError(
            f"No se pudo extraer la MAC de ether1 en {self.hostname}"
        )

class CiscoDevice(NetworkDevice):
    """Representa un dispositivo Cisco IOS."""

    def get_connection_config(self) -> Dict[str, Any]:
        """Retorna la configuración de conexión para Cisco IOS."""
        config = self.connection_params.copy()
        config["device_type"] = "cisco_ios"
        return config

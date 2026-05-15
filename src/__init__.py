"""TFG ASIR — Automatización de la configuración de una WAN con Python y Ansible."""

from .connector import DeviceConnectionError, DeviceConnector
from .models import CiscoDevice, MikroTikDevice, NetworkDevice

__all__ = [
    "CiscoDevice",
    "DeviceConnectionError",
    "DeviceConnector",
    "MikroTikDevice",
    "NetworkDevice",
]

__version__ = "0.1.0"

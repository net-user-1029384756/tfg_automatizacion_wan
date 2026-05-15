"""Tests unitarios de los modelos de dispositivo."""

from __future__ import annotations

import pytest

<<<<<<< HEAD
from tfg_automatizacion_wan.models import (
=======
from src.models import (
>>>>>>> ca60712 (feat: establish management network with sw-gest and verify connectivity to R1-R4)
    CiscoDevice,
    MikroTikDevice,
    NetworkDevice,
)


def test_network_device_es_abstracta():
    """No se puede instanciar la clase base directamente."""
    with pytest.raises(TypeError):
        NetworkDevice("R0", "10.0.0.1", "admin", "pwd")  # type: ignore[abstract]


def test_mikrotik_device_type():
    """MikroTik debe declarar device_type=mikrotik_routeros para Netmiko."""
    device = MikroTikDevice("R1", "192.168.99.10", "admin", "pwd")
    config = device.get_connection_config()
    assert config["device_type"] == "mikrotik_routeros"
    assert config["host"] == "192.168.99.10"
    assert config["username"] == "admin"
    assert config["password"] == "pwd"
    assert config["port"] == 22


def test_cisco_device_type():
    """Cisco debe declarar device_type=cisco_ios para Netmiko."""
    device = CiscoDevice("SW1", "192.168.99.20", "cisco", "cisco")
    config = device.get_connection_config()
    assert config["device_type"] == "cisco_ios"
    assert config["host"] == "192.168.99.20"


def test_get_connection_config_no_muta_estado_interno():
    """Llamar a get_connection_config no debe alterar connection_params."""
    device = MikroTikDevice("R1", "192.168.99.10", "admin", "pwd")
    snapshot = dict(device.connection_params)
    _ = device.get_connection_config()
    assert device.connection_params == snapshot
    assert "device_type" not in device.connection_params

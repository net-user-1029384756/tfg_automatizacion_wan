"""Tests del DeviceConnector con mocks (sin router real)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

from tfg_automatizacion_wan.connector import (
    DeviceConnectionError,
    DeviceConnector,
)
from tfg_automatizacion_wan.models import MikroTikDevice


@pytest.fixture
def device() -> MikroTikDevice:
    """Dispositivo de prueba reutilizable."""
    return MikroTikDevice("R1", "192.168.99.10", "admin", "pwd")


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_context_manager_abre_y_cierra(mock_handler, device):
    """El with debe llamar a ConnectHandler y luego a disconnect()."""
    fake_conn = MagicMock()
    mock_handler.return_value = fake_conn

    with DeviceConnector(device) as conn:
        assert conn.is_connected is True

    mock_handler.assert_called_once()
    fake_conn.disconnect.assert_called_once()


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_run_envía_comando(mock_handler, device):
    """run() debe delegar en send_command y devolver su salida."""
    fake_conn = MagicMock()
    fake_conn.send_command.return_value = "name: R1"
    mock_handler.return_value = fake_conn

    with DeviceConnector(device) as conn:
        output = conn.run("/system identity print")

    assert output == "name: R1"
    fake_conn.send_command.assert_called_once_with(
        "/system identity print", read_timeout=15
    )


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_configure_envía_lista(mock_handler, device):
    """configure() debe delegar en send_config_set."""
    fake_conn = MagicMock()
    fake_conn.send_config_set.return_value = "ok"
    mock_handler.return_value = fake_conn

    cmds = ["/ip address add address=10.0.0.1/30 interface=ether2"]
    with DeviceConnector(device) as conn:
        conn.configure(cmds)

    fake_conn.send_config_set.assert_called_once_with(cmds)


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_run_sin_conexion_falla(mock_handler, device):
    """Llamar a run() fuera de un with debe lanzar DeviceConnectionError."""
    conn = DeviceConnector(device)
    with pytest.raises(DeviceConnectionError):
        conn.run("/system identity print")


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_auth_falla_se_transforma(mock_handler, device):
    """Una excepción de autenticación de Netmiko se convierte en DeviceConnectionError."""
    mock_handler.side_effect = NetmikoAuthenticationException("bad password")

    with pytest.raises(DeviceConnectionError, match="autenticación"):
        with DeviceConnector(device):
            pass


@patch("tfg_automatizacion_wan.connector.ConnectHandler")
def test_timeout_se_transforma(mock_handler, device):
    """Un timeout de Netmiko se convierte en DeviceConnectionError."""
    mock_handler.side_effect = NetmikoTimeoutException("no route")

    with pytest.raises(DeviceConnectionError, match="Timeout"):
        with DeviceConnector(device):
            pass

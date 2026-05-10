# TFG — Automatización de la configuración de una WAN

Automatización de la configuración y despliegue de una WAN multi-fabricante
(MikroTik RouterOS y, opcionalmente, Cisco IOS) y de los equipos cliente
asociados, usando **Python 3.12** y **Ansible Core**.

Trabajo de Fin de Grado del CFGS de Administración de Sistemas Informáticos en
Red (Mariana Sanz, 2025/26) — Martín Gardachal Rodríguez.

## Stack

- Python 3.12 (POO, type hints, PEP 8)
- [Netmiko](https://github.com/ktbyers/netmiko) para SSH a dispositivos de red
- Ansible Core (desde WSL) para configuración declarativa
- GNS3 + VirtualBox sobre Windows 11 Pro
- MikroTik CHR 7.21 (router/switch principal del laboratorio)

## Instalación rápida

```bash
# Desde la raíz del repo, con Python 3.12 instalado:
python -m venv .venv
source .venv/bin/activate         # WSL/Linux
# .venv\Scripts\activate          # PowerShell

pip install -e ".[dev]"
```

## Configuración

1. Copia `.env.example` a `.env` y rellena las credenciales:

   ```bash
   cp .env.example .env
   ```

2. Ajusta `inventory/devices.yml` con las IPs reales de tus dispositivos.

## Bootstrap manual del laboratorio (una sola vez por router)

GNS3 no asigna IP automática a los nodos. Antes de poder usar este código,
hay que dejar accesible cada router por SSH. Pasos para R1:

1. Crear en Windows un **Microsoft KM-TEST Loopback Adapter** con IP estática
   `192.168.99.1/24`.
2. En GNS3, conectar el nodo Cloud a ese Loopback Adapter.
3. Abrir la consola de R1 (telnet desde GNS3) y ejecutar:

   ```routeros
   /ip address add address=192.168.99.10/24 interface=ether1
   /user set admin password=Tfg2026!
   /ip service enable ssh
   /system identity set name=R1
   ```

4. Comprobar desde Windows/WSL: `ssh admin@192.168.99.10`.

A partir de aquí, todo el resto de la configuración se hace desde Python.

## Uso

```bash
tfg-wan                                  # sondea todos los dispositivos
tfg-wan -i inventory/devices.yml -v      # ruta personalizada y modo DEBUG
```

## Tests

```bash
pytest
ruff check .
```

## Estructura

```
tfg-automatizacion-wan/
├── src/tfg_automatizacion_wan/
│   ├── __init__.py
│   ├── main.py          # CLI / entrypoint
│   ├── models.py        # NetworkDevice, MikroTikDevice, CiscoDevice
│   ├── connector.py     # DeviceConnector (Netmiko + context manager)
│   └── utils.py         # logging y carga de inventario
├── tests/               # tests unitarios con mocks
├── inventory/           # inventarios YAML
├── topology/            # proyecto GNS3
├── docs/                # memoria, capturas y referencias
├── pyproject.toml
└── README.md
```

## Licencia

Ver [`LICENSE.txt`](LICENSE.txt).

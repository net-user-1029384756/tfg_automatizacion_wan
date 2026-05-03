# Fase 1: Diseño de la Topología WAN

## 1. Esquema de Red
El proyecto se basa en una arquitectura multi-sede conectada mediante una WAN simulada.

### Sedes y Dispositivos
- **Sede Central (HQ):**
  - **Router de Borde:** MikroTik CHR (OS v7.21).
  - **Switch de Acceso:** Cisco IOSv.
  - **Equipos:** 1x Ubuntu Server, 1x Windows 10.
- **Sede Remota (Branch):**
  - **Router:** MikroTik CHR.
  - **Equipos:** 1x Ubuntu Desktop.

## 2. Direccionamiento IP (Plan Inicial)
- **Red de Gestión:** 192.168.1.0/24 (Para acceso SSH desde el host).
- **Enlace WAN (HQ <-> Branch):** 10.0.0.0/30.
- **Sede Central (VLANs):**
  - VLAN 10 (Datos): 192.168.10.0/24.
  - VLAN 20 (Voz/Gestión): 192.168.20.0/24.
- **Sede Remota:**
  - LAN: 192.168.100.0/24.

## 3. Protocolos de Red
- **Enrutamiento:** OSPF v2 para conectividad entre sedes.
- **Conmutación:** 802.1Q (Trunking) entre MikroTik y Cisco en la Sede Central.
- **Seguridad:** Listas de control de acceso (ACLs) y Firewall básico en MikroTik.

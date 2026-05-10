# Guía de documentación — TFG ASIR

## Formato obligatorio (plantilla del centro)
- Fuente: Calibri 11
- Márgenes: 2,5 cm arriba/abajo, 3 cm izquierda/derecha
- Interlineado: 1.15
- Texto justificado a ambos lados
- Extensión: mínimo 40 páginas sin contar anexos
- Entrega: PDF
- Incluir: portada, índice numerado, encabezado, pie de página, numeración y bibliografía

## Estructura del documento

### 1. Portada
- Nombre: Martín Gardachal Rodríguez
- Ciclo: CFGS Administración de Sistemas Informáticos en Red
- Centro: Mariana Sanz
- Curso: 2025/26
- Título: "Automatización de la configuración de racks de red y equipos cliente mediante Python y Ansible"

### 2. Índice
- Índice numerado y automatizado (cada vez que se añade un titulo y asi se actualiza solo).

### 3. Introducción
- Contextualización del problema: complejidad de gestionar infraestructuras multi-fabricante manualmente.
- Por qué Python + Ansible es la solución adecuada.
- Alcance del proyecto: qué cubre y qué queda fuera.
- ~1-2 páginas.

### 4. Objetivos del proyecto
- Objetivo general: automatizar configuración y despliegue de la infraestructura completa.
- Objetivos específicos: uno por cada bloque funcional (VLANs, OSPF, clientes Linux, clientes Windows, servidores...).
- Beneficios esperados: reducción de errores humanos, tiempo de despliegue, homogeneidad.

### 5. Requisitos previos
- Hardware: CPU con VT-x/AMD-V, 16GB RAM DDR4/5, SSD NVMe, tarjeta de red.
- Software: Windows 11 Pro, VirtualBox, GNS3, WSL2, Python 3.12, Ansible Core, VS Code.
- Justificar cada requisito brevemente.

### 6. Enumeración y desarrollo de las etapas
Esta es la sección principal (~25-30 páginas). Estructura por fases:

  - **Fase 1 — Diseño de la topología**: diagrama de red, decisiones de diseño, direccionamiento IP.
  - **Fase 2 — Entorno de virtualización**: configuración de VirtualBox + GNS3, importación de ISOs.
  - **Fase 3 — Automatización de red con Python**: clases, conexión SSH, configuración de VLANs/OSPF. Incluir fragmentos de código clave y capturas de resultado.
  - **Fase 4 — Automatización con Ansible**: estructura de roles, playbooks, Vault. Mostrar ejecución y output.
  - **Fase 5 — Equipos cliente y servidores**: detección de SO, aplicación de políticas, capturas de antes/después.
  - **Fase 6 — Pruebas y validación**: resultados de pytest, ansible-lint, pruebas de conectividad end-to-end.

Para cada fase incluir:
  - Explicación técnica de qué se hizo y por qué.
  - Capturas de pantalla relevantes (con pie de foto numerado).
  - Fragmentos de código si aportan valor explicativo.
  - Problemas encontrados durante esa fase y cómo se resolvieron.

### 7. Conclusiones
- Reflexión sobre si se cumplieron los objetivos.
- Problemas encontrados y soluciones aplicadas.
- Puntos fuertes y débiles del proyecto.
- Posibles mejoras futuras (GUI, inventario dinámico, CI/CD completo...).
- ~1-2 páginas.

### 8. Bibliografía y referencias
- Formato APA 7.
- Incluir: documentación oficial de Netmiko, Ansible, MikroTik, Cisco, GNS3, Python.
- Ir añadiendo referencias conforme se consulten durante el desarrollo.

---

## Cómo usar este fichero con Gemini

Cuando termines una fase técnica, dile:
> "Lee docs/DOCUMENTO.md y dime qué debo documentar de lo que acabamos de hacer en [fase X]: qué capturas hacer, qué explicar y redáctame el texto técnico para esa sección."

Gemini redactará el texto en markdown. Tú lo adaptas y lo pegas en el Word.
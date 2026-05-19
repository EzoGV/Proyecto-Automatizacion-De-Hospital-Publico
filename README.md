README.md

# Pipeline DataOps - Gestión de Registros de Pacientes
**Hospital Público - Proyecto ITY1101**

Este proyecto implementa un pipeline de datos automatizado bajo la metodología DataOps para la consolidación, limpieza y carga de registros médicos desde fuentes heterogéneas hacia un repositorio centralizado.

## Estado de la Infraestructura
Actualmente, el entorno se encuentra **operativo**. Se ha utilizado Oracle database para mejorar la compatibilidad con estándares corporativos de salud.

### Tecnologías Utilizadas
* **Base de Datos:** Oracle Database (Dockerized)
* **Lenguaje:** Python 3.10+
* **Orquestación:** Docker & Docker Compose
* **Gestión:** Metodología PMBOK + Sprints Ágiles

## Requisitos Previos
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución.
* Git instalado.

##  Configuración del Entorno

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/Proyecto-Automatizacion-De-Hospital-Publico.git](https://github.com/TU_USUARIO/Proyecto-Automatizacion-De-Hospital-Publico.git)
   cd Proyecto-Automatizacion-De-Hospital-Publico

2. **Como levantar el Docker**
   ```bash
   docker compose up -d
   docker ps para verificar que esta todo en orden 

3. **Librerias y levantar entorno virtual**
   ```bash
   python -m venv venv
   pip install oracledb python-dotenv
   pip install customtkinter
   pip install cryptography 'Para cumplir con el cifrado AES-256'

4. **Comando para correr test unitario**
   ```bash   
   python test.py
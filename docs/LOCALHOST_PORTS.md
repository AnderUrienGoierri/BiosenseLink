# Guía de Puertos y Servicios en Localhost (Windows)

Esta guía explica cómo identificar qué servicios y procesos están utilizando los puertos de red en `localhost` bajo el sistema operativo Windows (usando PowerShell o el Símbolo del Sistema).

---

## 1. Puertos Activos Detectados

El siguiente listado muestra los puertos TCP que se encontraban en estado de escucha (`LISTENING`) en este equipo:

| Puerto | PID | Proceso / Servicio | Descripción |
| :--- | :--- | :--- | :--- |
| **80** | 6368 | `httpd` | Servidor Web Apache (HTTP) |
| **100** | 9252 | `SamsungFindWindowsService` | Servicio de Samsung Find en Windows |
| **135** | 1488 | `svchost` | Microsoft Remote Procedure Call (RPC) |
| **139** | 4 | `System` | NetBIOS Session Service |
| **445** | 4 | `System` | Microsoft-DS (SMB / Compartición de archivos) |
| **1716** | 12540 | `kdeconnectd` | Servicio de KDE Connect |
| **2179** | 3668 | `vmms` | Hyper-V Virtual Machine Management Service |
| **3000** | 20044 | `com.docker.backend` | Docker Backend (usualmente Apps Web / APIs en desarrollo) |
| **3030** | 20044 | `com.docker.backend` | Docker Backend |
| **3031** | 20044 | `com.docker.backend` | Docker Backend |
| **3306** | 9060 | `mysqld` | Servidor de base de datos MySQL |
| **33060** | 9060 | `mysqld` | Puerto administrativo/X Protocol de MySQL |
| **5040** | 10784 | `svchost` | Servicio del sistema Windows (Delivery Optimization) |
| **5050** | 35728 | `wslrelay` | Relé de red para WSL (Windows Subsystem for Linux) |
| **5432** | 35728 | `wslrelay` | Puerto por defecto de **PostgreSQL** (redireccionado desde WSL) |
| **5678** | 20044 | `com.docker.backend` | Docker Backend |
| **7260** | 12680 | SECOND_SCREEN | Servicio de pantalla secundaria (Samsung/Windows) |
| **7679** | 20832 | `GoogleDriveFS` | File Stream de Google Drive |
| **8080** | 20044 | `com.docker.backend` | Docker Backend (Servidor Web Alternativo / Contenedor) |
| **11434** | 20044 | `com.docker.backend` | Puerto por defecto de **Ollama** (ejecutándose en Docker) |
| **51501** | 27572 | `Antigravity IDE` | Entorno de desarrollo (IDE) |
| **51502** | 27572 | `Antigravity IDE` | Entorno de desarrollo (IDE) |

---

## 2. Comandos para Consultar Puertos

### Opción A: Usando PowerShell (Recomendado)

PowerShell permite consultar y formatear los resultados directamente relacionando las conexiones con los nombres de los procesos.

**Comando rápido:**
```powershell
Get-NetTCPConnection -State Listen | ForEach-Object { 
    [PSCustomObject]@{ 
        Port = $_.LocalPort; 
        PID = $_.OwningProcess; 
        Process = (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name 
    } 
} | Sort-Object Port -Unique | Format-Table -AutoSize
```

### Opción B: Usando el Símbolo del Sistema (CMD)

Si necesitas usar la consola clásica de Windows o comandos básicos:

1. **Listar todos los puertos en escucha y sus PIDs:**
   ```cmd
   netstat -ano | findstr LISTENING
   ```

2. **Identificar a qué aplicación pertenece un PID específico:**
   *(Reemplaza `<PID>` por el número que obtuviste en el paso anterior)*
   ```cmd
   tasklist /FI "PID eq <PID>"
   ```

---

## 3. Detener / Liberar un Puerto Ocupado

Si necesitas liberar un puerto que está siendo ocupado por un proceso colgado o no deseado:

1. Obtén el **PID** del proceso usando los comandos anteriores.
2. Termina el proceso usando su PID:
   * **En PowerShell:**
     ```powershell
     Stop-Process -Id <PID> -Force
     ```
   * **En CMD (como administrador):**
     ```cmd
     taskkill /PID <PID> /F
     ```

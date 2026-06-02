# Documentacion Tecnica de Procesamiento Digital de Senales

## Filtros Digitales Implementados en BiosenseLink

### 1. Filtros Butterworth IIR

Los filtros Butterworth se caracterizan por tener una respuesta en magnitud
**maximamente plana** en la banda de paso. Esto significa que no introducen
rizados (ripple) que distorsionen la morfologia de las ondas PQRST.

El filtro Butterworth de orden N tiene una funcion de transferencia cuya
magnitud al cuadrado es:

```
|H(jw)|^2 = 1 / (1 + (w/wc)^(2N))
```

donde `wc` es la frecuencia de corte y `N` es el orden del filtro.

### Variantes implementadas:

| Filtro | Banda de Paso | Uso Clinico | Norma |
|:---|:---|:---|:---|
| Paso Banda 0.5-40 Hz | 0.5 - 40 Hz | ECG diagnostico estandar | IEC 60601-2-25 |
| Paso Banda 0.05-100 Hz | 0.05 - 100 Hz | Alta fidelidad diagnostica | AHA 2007 |
| Paso Banda 0.5-150 Hz | 0.5 - 150 Hz | Monitorizacion Holter | AAMI EC11 |
| Paso Bajo 25 Hz | DC - 25 Hz | Eliminacion agresiva de ruido | Investigacion |
| Paso Bajo 40 Hz | DC - 40 Hz | Pre-procesamiento para PQRST | Clinico |
| Paso Alto 0.5 Hz | 0.5 Hz - Nyquist | Eliminar deriva baseline | Ambulatorio |
| Paso Alto 1.0 Hz | 1.0 Hz - Nyquist | Eliminar deriva agresiva | Investigacion |

### 2. Filtro Notch (Elimina-Banda)

Elimina interferencias de red electrica a frecuencias discretas:
- **50 Hz** para la red electrica europea.
- **60 Hz** para la red electrica americana.

El factor de calidad Q = 30 proporciona un notch estrecho que elimina
solo la frecuencia objetivo sin afectar componentes espectrales adyacentes.

### 3. Filtrado de Fase Cero (filtfilt)

Todos los filtros aplican la tecnica de **filtrado forward-backward**
(filtfilt de SciPy), que procesa la senal en ambos sentidos temporales.
Esto cancela completamente el desfase de fase del filtro IIR, preservando
la alineacion temporal exacta de las ondas PQRST.

Si un filtro Butterworth de orden 4 se aplica una vez (lfilter), introduce
un desfase de grupo no constante que distorsiona los intervalos PR y QT.
Con filtfilt, el desfase neto es exactamente cero en todas las frecuencias.

> **Referencia:**
> Gustafsson F. "Determining the initial states in forward-backward
> filtering." IEEE Trans Signal Process. 1996;44(4):988-992.

### 4. Pipelines Predefinidos

#### Pipeline Clinico Estandar
```
Senal Cruda -> Notch 50Hz (Q=30) -> Butterworth Paso Banda (0.5-40 Hz, orden 4)
```
Este pipeline cumple con la norma IEC 60601-2-25 para equipos de ECG
diagnostico y es el pipeline por defecto de BiosenseLink.

#### Pipeline de Monitorizacion
```
Senal Cruda -> Notch 50Hz (Q=30) -> Butterworth Paso Banda (0.5-150 Hz, orden 3)
```
Utilizado en monitores Holter y sistemas de telemetria ambulatoria donde
se requiere la banda completa para analisis de arritmias de alta frecuencia.

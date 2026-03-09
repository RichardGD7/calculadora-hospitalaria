# Documento Técnico — Calculadora de Capacidad Sanoviv

**Versión:** 1.1
**Fecha:** Marzo 2026
**Desarrollado por:** Arkode

---

## 1. Descripción General

La Calculadora de Capacidad Sanoviv es una aplicación web que permite gestionar y verificar la capacidad operativa del hospital. Sus funciones principales son:

- **Registro de pacientes actuales** por programa y semana de estancia (W1, W2, W3)
- **Visualización del uso real de recursos** (profesionales y físicos) calculado con el consumo específico por semana
- **Verificación de admisión** de nuevos pacientes validando que los recursos disponibles sean suficientes para admitirlos en la semana 1 de su programa
- **Optimización** (complementaria) que sugiere cuántos pacientes adicionales podrían admitirse usando promedios semanales

La aplicación no almacena datos de pacientes individuales ni información personal. Solo trabaja con cantidades agregadas por programa.

---

## 2. Stack Tecnológico

| Componente | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.10+ |
| Framework web | Streamlit | 1.52.1 |
| Manipulación de datos | Pandas | 2.3.3 |
| Visualización | Plotly | 6.5.0 |
| Cálculo numérico | NumPy | 2.2.6 |
| Motor de optimización | PuLP (solver CBC) | 3.2.1 |

**No se utilizan** bases de datos, APIs externas, servicios en la nube ni conexiones a internet en tiempo de ejecución. Toda la información reside en archivos locales.

---

## 3. Arquitectura de Archivos

```
calculadora-hospitalaria/
├── app.py                  # Interfaz de usuario (Streamlit) — 2,456 líneas
├── optimizador_v2.py       # Motor de optimización ILP — 658 líneas
├── BD_sanoviv.py           # Base de datos (archivo Python) — 7,605 líneas
├── requirements.txt        # Dependencias del proyecto
├── .streamlit/
│   └── config.toml         # Configuración de tema (light)
├── .devcontainer/
│   └── devcontainer.json   # Configuración para desarrollo en contenedor
└── LICENSE
```

### 3.1 BD_sanoviv.py — Fuente de Datos

Archivo Python que contiene todas las definiciones operativas como estructuras de datos. No es una base de datos tradicional — es código Python que se importa al iniciar la aplicación.

**Contenido:**
- **catalogo_actividades** — 60+ actividades médicas con tipo, duración, recursos requeridos
- **programas** — 23 programas (11 base + 12 extensiones) con sus actividades y distribución semanal
- **recursos_profesionales** — Personal médico con capacidades semanales (horas)
- **recursos_fisicos** — Instalaciones con capacidades semanales (horas)

**Distribución semanal:** Cada actividad incluye un campo `cantidad_por_semana` que define cuántas veces ocurre en cada semana del programa. Esto permite calcular el consumo real de recursos según en qué semana se encuentra cada paciente.

**Modificación:** El usuario administrador puede editar estos datos desde la UI. Al guardar, se regenera el archivo `BD_sanoviv.py` completo.

### 3.2 optimizador_v2.py — Motor de Cálculo

Contiene la lógica de cálculo sin interfaz visual:

| Función | Propósito |
|---|---|
| `construir_modelo_datos()` | Calcula consumo promedio semanal por programa (para optimización) |
| `construir_modelo_datos_semana(semana)` | Calcula consumo real de una semana específica (para verificación) |
| `ejecutar_optimizacion(pacientes)` | Resuelve modelo ILP para maximizar admisiones (promedios) |
| `verificar_admision_semana(pacientes, solicitudes)` | Verifica si caben nuevos pacientes con consumo real por semana |

### 3.3 app.py — Interfaz de Usuario

Aplicación Streamlit con las siguientes pestañas (en orden de aparición):

| Pestaña | Función |
|---|---|
| Patients | Registro de pacientes actuales por programa y semana (W1/W2/W3), agrupados por duración del programa. Botón para ejecutar optimización |
| Resources | Uso real de recursos calculado con consumo específico por semana, independiente del optimizador |
| Verify Admission | Verificación de factibilidad para admitir nuevos pacientes (siempre en semana 1) |
| Optimization Results | Resultados del optimizador basado en promedios semanales (con banner de advertencia) |
| Administration | Gestión de programas, actividades y recursos (requiere contraseña) |

---

## 4. Flujos Funcionales

### 4.1 Flujo Principal — Verificar Admisión

```
1. Usuario ingresa pacientes actuales por programa y semana en tab "Patients"
   (ej. Cancer Treatment: 2 en W1, 1 en W2, 0 en W3)
     ↓
2. La app calcula el consumo real de recursos sumando las contribuciones
   de cada semana según la distribución de actividades
     ↓
3. Usuario va a "Verify Admission" y solicita admitir N pacientes de un programa
   (siempre entran en semana 1)
     ↓
4. El sistema calcula si los recursos disponibles son suficientes
   considerando los pacientes existentes en todas sus semanas
     ↓
5. Muestra resultado: FACTIBLE / NO FACTIBLE con detalle por recurso limitante
```

### 4.2 Flujo de Administración

```
1. Admin ingresa contraseña → accede a pestaña Administration
     ↓
2. Puede editar: programas, actividades (con distribución semanal W1/W2/W3), recursos
     ↓
3. Puede crear nuevos programas con actividades y distribución semanal
     ↓
4. Al guardar → se regenera BD_sanoviv.py y se recarga la aplicación
```

### 4.3 Cálculo de Consumo de Recursos

Para cada paciente, el consumo semanal de un recurso se calcula usando la distribución real por semana:

```
consumo_horas = cantidad_actividades_en_esa_semana × duración_minutos / 60
```

Ejemplo: "Medical Follow-up Consultation" en Cancer Treatment (3 semanas):
- Semana 1: 4 consultas × 30 min = 2.0 horas
- Semana 2: 5 consultas × 30 min = 2.5 horas
- Semana 3: 3 consultas × 30 min = 1.5 horas

Un paciente en semana 1 consume más que uno en semana 3 para esta actividad. El sistema suma las contribuciones de todos los pacientes según en qué semana se encuentra cada uno.

### 4.4 Cálculo de Semanas por Programa

La duración en semanas se calcula con redondeo hacia arriba:
- 7 días = 1 semana
- 8 días = 2 semanas
- 14 días = 2 semanas
- 21 días = 3 semanas

---

## 5. Seguridad y Acceso

### 5.1 Autenticación

- **Modo Viewer** (por defecto): Acceso a todas las pestañas excepto Administration
- **Modo Administrator**: Requiere contraseña para acceder a la gestión de datos
- La contraseña se define como constante en `app.py` (variable `ADMIN_PASSWORD`)

### 5.2 Datos

- **No hay datos personales** de pacientes — solo cantidades agregadas por programa
- **No hay conexión a internet** en tiempo de ejecución
- **No hay base de datos** — los datos residen en `BD_sanoviv.py` como código Python
- **No hay APIs expuestas** — la aplicación es solo una interfaz web local
- **No hay almacenamiento de sesiones** — los datos de pacientes ingresados viven en la sesión del navegador

### 5.3 Dependencias

Todas las dependencias son librerías open-source ampliamente utilizadas:

| Librería | Licencia | Uso |
|---|---|---|
| Streamlit | Apache 2.0 | Framework web |
| Pandas | BSD 3-Clause | Tablas de datos |
| Plotly | MIT | Gráficos |
| NumPy | BSD 3-Clause | Cálculos |
| PuLP | BSD 2-Clause | Optimización |

No se utilizan dependencias propietarias ni servicios de terceros.

---

## 6. Despliegue

### 6.1 Requisitos del Servidor

- **Python** 3.10 o superior
- **RAM**: 512 MB mínimo (la aplicación es ligera)
- **Disco**: < 50 MB para código y dependencias
- **Puerto**: 8501 (configurable, puerto por defecto de Streamlit)
- **SO**: Linux, Windows o macOS

### 6.2 Instalación

```bash
# Clonar repositorio
git clone <url-del-repositorio>
cd calculadora-hospitalaria

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 6.3 Ejecución

```bash
streamlit run app.py --server.port 8501
```

Para acceso en red local:
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 6.4 Configuración Opcional

El archivo `.streamlit/config.toml` permite ajustar:
- Tema visual (actualmente: light)
- Puerto del servidor
- Opciones de CORS y XSRF

---

## 7. Consideraciones para el Equipo de TI

1. **La aplicación no requiere acceso a internet** una vez instalada. Todas las dependencias se instalan localmente.

2. **No hay persistencia de sesión** — los datos ingresados por el usuario (pacientes actuales por semana) viven en la sesión del navegador y se pierden al cerrar. Los datos base (programas, recursos) persisten en `BD_sanoviv.py`.

3. **Backup**: El único archivo que cambia en producción es `BD_sanoviv.py` (cuando el admin guarda cambios desde la pestaña Administration). Se recomienda mantener backups periódicos de este archivo.

4. **Actualizaciones**: Se realizan vía `git pull` desde el repositorio. No hay migraciones de base de datos. Los cambios hechos por el admin en `BD_sanoviv.py` se sobreescribirán con un `git pull`, por lo que se debe respaldar antes de actualizar.

5. **Monitoreo**: Streamlit genera logs en la consola. Para producción, se recomienda ejecutar detrás de un proceso supervisor (systemd, PM2, etc.).

6. **HTTPS**: Streamlit no incluye SSL nativo. Si se requiere HTTPS, usar un reverse proxy (Nginx, Apache, Caddy) frente a la aplicación.

7. **Permisos de escritura**: La aplicación necesita permisos de escritura sobre `BD_sanoviv.py` en el directorio de instalación para que el admin pueda guardar cambios.

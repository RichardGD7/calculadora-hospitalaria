# Sanoviv - Sistema de Optimización de Capacidad de Pacientes

## Resumen Ejecutivo

**Sanoviv Capacity Optimizer** es una herramienta web que utiliza programación lineal para determinar el número máximo de pacientes que pueden ser admitidos en programas de tratamiento especializados, respetando las restricciones de disponibilidad del personal médico y la capacidad de las instalaciones.

---

## Alcance del Proyecto

### Objetivo Principal

Desarrollar un sistema de planificación y optimización de capacidad para el Instituto Médico Sanoviv que permita:

- **Maximizar** la utilización de la capacidad de pacientes en todos los programas de tratamiento
- **Optimizar** la asignación de pacientes basada en niveles de prioridad de cada programa
- **Respetar** las restricciones de disponibilidad de recursos (profesionales y físicos)
- **Identificar** cuellos de botella y excesos de capacidad en recursos
- **Apoyar** las decisiones de planificación estratégica del instituto

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Frontend** | Streamlit (Framework web para Python) |
| **Visualización** | Plotly (gráficos interactivos) |
| **Procesamiento de Datos** | Pandas |
| **Motor de Optimización** | PuLP (librería de optimización lineal) |
| **Solver** | CBC (Coin-or-branch and cut) |
| **Lenguaje** | Python 3.10+ |

### Arquitectura

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                          INTERFAZ DE USUARIO                                  │
│                          (Streamlit - app.py)                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────────────────────┐ │
│  │  Resumen  │  │ Pacientes │  │  Recursos │  │     Verificar Admisión      │ │
│  │ Ejecutivo │  │           │  │           │  │                             │ │
│  └───────────┘  └───────────┘  └───────────┘  └─────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         MOTOR DE OPTIMIZACIÓN                                 │
│                         (optimizador.py)                                      │
│  • Programación Lineal Entera (ILP)    • Verificación de Factibilidad         │
│  • Solver CBC vía PuLP                 • Análisis de Recursos Limitantes      │
│  • Análisis de Capacidad               • Cálculo de Impacto en Recursos       │
└───────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                             CAPA DE DATOS                                     │
│                         (datos_sanoviv_generado.py)                           │
│  • 11 Programas de Tratamiento                                                │
│  • 57 Recursos (23 Profesionales + 34 Físicos)                                │
│  • Matrices de Consumo                                                        │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Módulos y Funcionalidades

### 1. Resumen Ejecutivo

Dashboard ejecutivo con visualizaciones clave:

- **KPIs principales**: Pacientes actuales, capacidad adicional, total proyectado, valor ponderado
- **Gráfico de barras apiladas**: Comparación de pacientes actuales vs. adicionales por programa
- **Gráficos de dona**: Distribución de utilización de recursos por categoría
- **Top 10 recursos**: Recursos más utilizados
- **Sistema de alertas**: Notificaciones para recursos sobre capacidad
- **Advertencia de recursos excedidos**: Banner prominente cuando hay recursos sobresaturados que fueron excluidos del modelo

### 2. Gestión de Pacientes

- Tabla editable para conteo de pacientes actuales por programa
- Visualización de valores de prioridad por programa
- Botón "Calcular Optimización" para ejecutar el solver
- Tabla de resultados: pacientes actuales, adicionales y total proyectado
- **Advertencia de recursos excedidos**: Banner de alerta cuando hay recursos sobresaturados
- **Sincronización en tiempo real**: Los cambios en la tabla se reflejan inmediatamente en todas las pestañas

### 3. Análisis de Recursos

- **Contador de pacientes totales**: Muestra el total de pacientes actuales en la parte superior
- Tabla detallada de utilización de recursos con filtrado por nivel de uso
- Seguimiento de capacidad, uso actual, uso adicional y uso total
- Indicadores de progreso basados en porcentaje
- Sección de alertas para recursos que exceden capacidad

### 4. Verificar Admisión (Nuevo)

Módulo interactivo para verificar la factibilidad de admitir pacientes específicos antes de su ingreso:

- **Formulario de solicitudes**: Selector de programa y cantidad de pacientes a verificar
- **Soporte multi-programa**: Permite agregar múltiples solicitudes de diferentes programas simultáneamente
- **Verificación de factibilidad**: Analiza si los recursos disponibles pueden soportar las admisiones solicitadas
- **Resultado visual claro**: Indicador de factible (verde) o no factible (rojo) con detalle por programa
- **Análisis de recursos limitantes**: Tabla detallada de recursos que impiden la admisión
- **Impacto en recursos**: Gráfico de barras mostrando el impacto proyectado en los 15 recursos más afectados
- **Información por programa**:
  - Pacientes actuales en el programa
  - Cantidad solicitada vs. máximo admisible
  - Déficit (si aplica)
  - Recurso específico que limita la admisión
- **Botón limpiar**: Elimina solicitudes y resultados anteriores

---

## Modelo de Datos

### Programas de Tratamiento (11)

| # | Programa |
|---|----------|
| 1 | Cancer Treatment |
| 2 | Lyme Disease & Co-Infections |
| 3 | Detox and Rejuvenation |
| 4 | Stem Cell Rejuvenation |
| 5 | NeuroFeedback Detox |
| 6 | Medical Treatment |
| 7 | Integrative Physical |
| 8 | Long COVID Treatment |
| 9 | Neuro Cognitive |
| 10 | Mycotoxin Detox |
| 11 | Microbiome Restore |

### Recursos Profesionales (23)

| Categoría | Recursos |
|-----------|----------|
| **Equipo Dental** | Asistente Dental, Dentista, Higienista Dental |
| **Equipo Médico** | Médico Oncólogo, Médico de guardia, Médico especialista, Médico Tratante |
| **Enfermería** | Enfermero - Hipertermia, Enfermero - Quirófano, Enfermero general |
| **Terapia y Bienestar** | Fisioterapeuta, Fisioterapeuta SPA, Psicólogo, Nutriólogo, Mind and Body Therapist, Instructor de Fitness, Quiropráctico |
| **Especializados** | Técnico de Colónicos, Técnico de Hiperbárica, Técnico Radiólogo, Terapeuta de Neurofeedback, Químico de I+D, Radiólogo |

### Recursos Físicos (34)

| Categoría | Recursos |
|-----------|----------|
| **Alojamiento** | Dormitorio, Cama de Quiet Room, Espacio de Comedor |
| **Instalaciones Médicas** | Consultorio Médico, Quirófano, Cuarto de Hospitalización, Cuarto de Flebotomía |
| **Equipo Diagnóstico** | CT Scan, Cuarto de Radiología, Resonancia, Rayos X Dental, Ultrasonido, Termógrafo |
| **Terapia Térmica** | Cámara Hiperbárica, Cámara de Hipertermia (cuerpo completo/regional), Sauna |
| **Tratamiento Especializado** | Consultorios (Fitness, Hidroterapia, MBT, Nutrición, Psicología, Quiropraxia), Cuarto de Ozono, Sala de Masaje SPA, Gabinetes de Spa |
| **Dental** | Unidad Dental de Evaluación, Unidad Dental de Tratamiento |
| **Otros** | Gastroenterología, Módulo de Neurofeedback, Reposet (centros de infusión) |

---

## Modelo de Optimización

### Tipo
Programación Lineal Entera (ILP)

### Función Objetivo
```
Maximizar: Σ(prioridad_j × pacientes_adicionales_j)
```

### Restricciones
```
Para cada recurso r:
Σ(consumo[r,j] × pacientes_adicionales[j]) ≤ capacidad_restante[r]
```

### Solver
CBC (Coin-or-branch and cut) vía PuLP

### Salida
Asignación óptima de enteros para cada programa

### Verificación de Factibilidad (Nuevo)

Función adicional `verificar_admision()` que permite consultar la factibilidad de admisiones específicas:

**Entrada:**
- `pacientes_actuales`: Lista con pacientes actuales por programa
- `solicitudes`: Diccionario `{índice_programa: cantidad}` con solicitudes a verificar

**Proceso:**
1. Calcula uso actual de cada recurso
2. Calcula uso adicional requerido por las solicitudes
3. Verifica si uso total proyectado excede capacidad
4. Identifica recursos limitantes y calcula déficit

**Salida:**
- `factible`: Booleano indicando factibilidad global
- `solicitudes_detalle`: Detalle por programa con máximo admisible y recurso limitante
- `recursos_limitantes`: Lista de recursos que exceden capacidad
- `impacto_recursos`: Impacto proyectado en cada recurso afectado

### Manejo de Recursos Excedidos

Cuando los pacientes actuales ya exceden la capacidad de algún recurso:

1. **Comportamiento del modelo**: Los recursos sobresaturados se excluyen de las restricciones de optimización para garantizar que el solver siempre encuentre una solución
2. **Sistema de advertencias**: Se muestran banners prominentes en las pestañas "Resumen Ejecutivo" y "Pacientes" indicando:
   - Número de recursos excedidos
   - Nombres de los recursos afectados
   - Advertencia de que los resultados podrían no ser confiables
   - Recomendación de resolver la sobresaturación primero

### Manejo de Errores

- **Try-catch en optimización**: Captura errores del solver y muestra mensaje amigable al usuario
- **Try-catch en verificación**: Captura errores en la función de verificación de admisión
- **Inicialización de estado**: Todas las variables de sesión se inicializan explícitamente para evitar errores de acceso

---

## Estructura del Proyecto

```
/sanoviv/
├── app.py                      # Aplicación web Streamlit (24 KB)
├── optimizador.py              # Modelo de optimización (6 KB)
├── datos_sanoviv_generado.py   # Configuración de datos (13 KB)
├── __pycache__/                # Caché de Python
└── .venv/                      # Entorno virtual de Python
```

---

## Propuesta de Valor

| Beneficio | Descripción |
|-----------|-------------|
| **Planificación basada en datos** | Elimina las conjeturas de la asignación de recursos |
| **Optimización por prioridad** | Alinea la admisión de pacientes con las prioridades estratégicas del programa |
| **Identificación de cuellos de botella** | Destaca qué recursos limitan el crecimiento |
| **Dashboards ejecutivos visuales** | Proporciona insights claros sobre la utilización de capacidad |
| **Planificación de escenarios** | Fácil ajuste de pacientes actuales y re-ejecución de optimización |
| **Verificación de admisiones** | Permite consultar la factibilidad de admitir pacientes específicos antes de su ingreso |

---

## Características Técnicas

### Interfaz de Usuario

- **Framework**: Streamlit
- **Estilo**: CSS personalizado con paleta de colores Arkode
  - Primario: #0F1C2E (Azul oscuro)
  - Secundario: #1E3A5F (Azul medio)
  - Acento: #FF6B5B (Coral/salmón)
  - Éxito: #10B981 (Verde)
  - Advertencia: #F59E0B (Amarillo)
  - Peligro: #EF4444 (Rojo)
- **Layout**: Diseño ancho, barra lateral colapsable
- **Visualización**: Gráficos interactivos con Plotly

### Modelo de Despliegue

- Aplicación Python independiente
- Sin base de datos backend requerida
- Acceso basado en navegador vía Streamlit
- Listo para despliegue institucional

---

## Estado Actual

### Configuración de Pacientes por Defecto

| Programa | Pacientes |
|----------|-----------|
| Cancer Treatment | 0 |
| Lyme Disease & Co-Infections | 0 |
| Detox and Rejuvenation | 0 |
| Stem Cell Rejuvenation | 0 |
| NeuroFeedback Detox | 0 |
| Medical Treatment | 0 |
| Integrative Physical | 0 |
| Long COVID Treatment | 0 |
| Neuro Cognitive | 0 |
| Mycotoxin Detox | 0 |
| Microbiome Restore | 0 |

**Capacidad Actual Total**: 0 pacientes (configuración inicial limpia)

---

## Posibles Integraciones Futuras

| Integración | Descripción |
|-------------|-------------|
| Sistema de gestión de pacientes | Obtener conteos reales de pacientes |
| Sistema de gestión de recursos | Actualizar capacidades y disponibilidad |
| Herramientas de Analytics/BI | Conexión con Tableau, Power BI para reportes |
| Notificaciones por email | Alertas cuando se exceda capacidad |
| Autenticación | Control de acceso de usuarios |
| Base de datos | Persistencia de datos históricos |

---

## Desarrollado por

**Arkode**

---

*Documento generado para presentación de alcance del proyecto*

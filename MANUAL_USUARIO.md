# Manual de Usuario — Calculadora de Capacidad Sanoviv

**Versión:** 1.0
**Fecha:** Marzo 2026
**Elaborado por:** Arkode

---

## 1. Introducción

La Calculadora de Capacidad Sanoviv es una herramienta web que permite gestionar la ocupación del hospital y verificar si es posible admitir nuevos pacientes sin exceder la capacidad de recursos disponibles.

**Funciones principales:**
- Registrar cuántos pacientes están activos en cada programa y en qué semana de tratamiento se encuentran
- Consultar el uso actual de recursos profesionales y físicos en tiempo real
- Verificar si es factible admitir nuevos pacientes antes de su ingreso
- Administrar programas, actividades y recursos (solo administradores)

> **Importante:** La aplicación no almacena datos de pacientes individuales. Solo trabaja con cantidades agregadas por programa de tratamiento.

---

## 2. Acceso a la Aplicación

### 2.1 Ingreso

Abra la URL de la aplicación en su navegador web. La aplicación se abre en **Modo Viewer** por defecto, que permite consultar toda la información operativa.

`[📸 Captura: Pantalla inicial de la aplicación mostrando la barra lateral con "Viewer Mode" y las pestañas principales]`

### 2.2 Modo Administrador

Para acceder a funciones de administración:

1. En la barra lateral izquierda, haga clic en **"Administrator Login"**
2. Ingrese la contraseña proporcionada por su equipo de TI
3. Haga clic en **"Login"**

Al activarse, aparecerá el mensaje **"Administrator Mode Active"** y se habilitará la pestaña **Administration**.

`[📸 Captura: Barra lateral mostrando el formulario de login de administrador]`

Para cerrar sesión de administrador, haga clic en el botón **"Logout"** en la barra lateral.

---

## 3. Pestañas de la Aplicación

La aplicación se organiza en pestañas. En modo Viewer se muestran 4 pestañas; en modo Administrador se agrega una quinta:

| Pestaña | Icono | Función |
|---|---|---|
| Patients | 👥 | Registrar pacientes actuales por programa y semana |
| Resources | 📈 | Consultar el uso de recursos en tiempo real |
| Verify Admission | 🔍 | Verificar si es factible admitir nuevos pacientes |
| Optimization Results | 📊 | Resultados del modelo de optimización (complementario) |
| Administration | ⚙️ | Gestión de programas, actividades y recursos |

---

## 4. Patients — Registro de Pacientes

Esta pestaña es el punto de partida. Aquí se registra cuántos pacientes están activos en cada programa y en qué semana de su tratamiento se encuentran.

### 4.1 Programas Base

Los programas base se agrupan por duración:

- **Programas de 1 semana:** Tienen una sola columna **W1** (semana 1)
- **Programas de 2 semanas:** Tienen columnas **W1** y **W2**
- **Programas de 3 semanas:** Tienen columnas **W1**, **W2** y **W3**

`[📸 Captura: Tabla de programas base de 3 semanas mostrando las columnas W1, W2, W3, Total y Priority]`

**Cómo registrar pacientes:**

1. Localice el programa de tratamiento en la tabla correspondiente
2. Haga clic en la celda de la semana donde se encuentra el paciente (W1, W2 o W3)
3. Ingrese el número de pacientes en esa semana
4. La columna **Total** se actualiza automáticamente (solo en programas de más de una semana)

> **Ejemplo:** Si tiene 2 pacientes de Cancer Treatment en su primera semana y 1 paciente en su segunda semana, ingrese **2** en W1 y **1** en W2.

### 4.2 Extensiones

Las extensiones se muestran en una tabla separada debajo de los programas base. Cada extensión indica a qué programa base pertenece y solo tiene columna **W1**.

`[📸 Captura: Tabla de extensiones mostrando las columnas Extension, Base Program, W1 y Priority]`

### 4.3 Botones de Acción

Al final de la pestaña se encuentran dos botones:

- **🔄 Calculate Optimization** — Ejecuta el modelo de optimización (los resultados se muestran en la pestaña "Optimization Results")
- **🗑️ Clear All Patients** — Reinicia todos los valores de pacientes a cero

`[📸 Captura: Botones "Calculate Optimization" y "Clear All Patients" al final de la pestaña]`

---

## 5. Resources — Uso de Recursos

Esta pestaña muestra en tiempo real cuánto se están utilizando los recursos del hospital con base en los pacientes registrados.

### 5.1 Recursos Profesionales

Tabla con el personal médico y terapéutico disponible:

| Columna | Descripción |
|---|---|
| Resource | Nombre del recurso (médico, terapeuta, etc.) |
| Capacity | Horas semanales disponibles |
| Current Usage | Horas consumidas por los pacientes actuales |
| % Current | Barra de progreso del porcentaje de uso |
| Status | **OK** si hay capacidad disponible, **Exceeded** si se superó |

`[📸 Captura: Tabla de recursos profesionales con barras de progreso y estados]`

### 5.2 Recursos Físicos

Misma estructura que los profesionales pero para instalaciones (salas, consultorios, equipos).

`[📸 Captura: Tabla de recursos físicos]`

### 5.3 Recursos Excedidos

Si algún recurso supera su capacidad, se muestra una sección adicional **"Exceeded Resources"** con el detalle del exceso en horas.

`[📸 Captura: Sección de recursos excedidos (puede generarse ingresando un número alto de pacientes en algún programa para forzar el exceso)]`

> **Nota:** El cálculo de uso considera la semana específica en la que se encuentra cada paciente. Un paciente en semana 1 puede consumir diferentes recursos que uno en semana 3 del mismo programa.

---

## 6. Verify Admission — Verificación de Admisión

Esta es la función más importante para la operación diaria. Permite verificar si es posible admitir nuevos pacientes sin exceder la capacidad de recursos.

### 6.1 Crear Solicitudes de Admisión

1. Seleccione el programa del paciente que desea admitir en **"Select program"**
   - Los programas base aparecen primero
   - Las extensiones aparecen con indentación y el nombre de su programa base entre paréntesis
2. Indique cuántos pacientes desea admitir en **"Number of patients"**
3. Haga clic en **"➕ Add"**

`[📸 Captura: Formulario de verificación de admisión mostrando el selector de programa y cantidad]`

Puede agregar múltiples solicitudes para distintos programas antes de verificar. Todas las solicitudes pendientes se muestran en la tabla **"Pending Requests to Verify"**.

`[📸 Captura: Tabla de solicitudes pendientes con al menos 2 programas agregados]`

> **Nota:** Los nuevos pacientes siempre ingresan en la **semana 1** de su programa. El sistema calcula automáticamente el impacto en recursos considerando las actividades de esa primera semana.

### 6.2 Verificar Factibilidad

Una vez agregadas todas las solicitudes, haga clic en **"🔍 Verify Feasibility"**.

El sistema evalúa si los recursos disponibles son suficientes para atender a los pacientes actuales **más** los nuevos solicitados, y muestra uno de dos resultados:

**Resultado FACTIBLE (verde):**

`[📸 Captura: Banner verde de "FEASIBLE" después de verificar una solicitud que sí cabe]`

**Resultado NO FACTIBLE (rojo):**

`[📸 Captura: Banner rojo de "NOT FEASIBLE" después de verificar una solicitud que excede capacidad]`

### 6.3 Detalle de Resultados

Cuando la admisión **no es factible**, el sistema muestra:

- **Detail by Program** — Tabla con el consumo total por programa (actuales + nuevos)
- **Resources Exceeding Capacity** — Lista de los recursos que serían excedidos
- **Resource Impact (Top 15)** — Gráfico de barras con los recursos más afectados

`[📸 Captura: Sección completa de detalle cuando una verificación no es factible, mostrando la tabla de programas, recursos excedidos y el gráfico de barras]`

### 6.4 Limpiar Solicitudes

Para reiniciar las solicitudes, haga clic en **"🗑️ Clear All"**.

---

## 7. Optimization Results — Resultados de Optimización

Esta pestaña muestra los resultados del modelo matemático de optimización, que calcula cuántos pacientes adicionales podrían admitirse teóricamente.

`[📸 Captura: Pestaña de Optimization Results mostrando el banner amarillo de advertencia y las métricas principales]`

> **⚠️ Nota importante:** El optimizador utiliza **promedios semanales** de consumo de recursos, no el consumo real por semana. Para decisiones de admisión diaria, utilice siempre la pestaña **"Verify Admission"** que calcula con datos reales por semana.

### 7.1 Métricas Principales

- **Current Patients** — Total de pacientes registrados
- **Additional Capacity** — Pacientes adicionales sugeridos por el optimizador

### 7.2 Cómo Ejecutar la Optimización

1. Vaya a la pestaña **Patients** y registre los pacientes actuales
2. Haga clic en **"🔄 Calculate Optimization"**
3. Los resultados aparecerán en esta pestaña

### 7.3 Tabla de Resultados

Muestra por cada programa:
- Pacientes actuales
- Pacientes adicionales sugeridos
- Total resultante
- Semana del programa

### 7.4 Alertas de Capacidad

Si algún recurso sería excedido, se muestra una sección de alertas con el detalle del exceso.

---

## 8. Administration — Gestión de Datos

> **Requiere:** Modo Administrador activo (ver sección 2.2)

La pestaña de administración permite gestionar todos los datos operativos de la aplicación, organizados en sub-pestañas.

### 8.1 Activity Catalog

Lista maestra de todas las actividades médicas disponibles.

`[📸 Captura: Tabla del catálogo de actividades mostrando Name, Type, Duration, y recursos]`

**Editar una actividad:**
1. Seleccione la actividad en el desplegable **"Select activity to edit"**
2. Modifique los campos necesarios (nombre, tipo, duración, recursos)
3. Haga clic en **"Update Activity"**

**Crear una actividad nueva:**
1. Desplácese a la sección **"Create New Activity"**
2. Complete todos los campos requeridos
3. Haga clic en **"Create Activity"**

### 8.2 Professional Resources

Tabla editable con el personal médico y sus capacidades semanales en horas.

`[📸 Captura: Tabla editable de recursos profesionales en la pestaña Administration]`

- Modifique directamente las celdas de la tabla para ajustar capacidades
- Los cambios solo se persisten al hacer clic en **"Save All Changes"**

### 8.3 Physical Resources

Tabla editable con las instalaciones y equipos del hospital.

`[📸 Captura: Tabla editable de recursos físicos en la pestaña Administration]`

### 8.4 Programs

Permite editar programas existentes y crear nuevos.

#### Editar Programa Existente

1. Seleccione el programa en la sub-pestaña **"Edit Existing Program"**
2. Modifique actividades, cantidades y distribución semanal (W1/W2/W3)
3. Los cambios se guardan con **"Save All Changes"**

`[📸 Captura: Editor de programa existente mostrando la tabla de actividades con columnas W1/W2/W3]`

#### Crear Nuevo Programa

El flujo de creación sigue estos pasos:

`[📸 Captura: Sub-pestaña "Create New Program" mostrando el banner azul informativo con los pasos]`

**Paso 1 — Definir el programa:**

1. Seleccione el **Tipo**:
   - **programa** — Programa independiente. El campo "Base Program" se deshabilita automáticamente
   - **extension** — Extensión de un programa existente. Debe seleccionar el programa base
2. Ingrese el **nombre** del programa
3. Configure la **duración en días** y la **prioridad**
4. Haga clic en el botón azul **"➕ Create Program"**

`[📸 Captura: Formulario de creación con tipo "programa" seleccionado, mostrando el campo "Base Program" deshabilitado]`

`[📸 Captura: Formulario de creación con tipo "extension" seleccionado, mostrando el campo "Base Program" habilitado con la lista de programas base]`

**Paso 2 — Agregar actividades:**

Después de crear el programa, aparece automáticamente el editor de actividades:

1. Seleccione actividades del catálogo
2. Ajuste la cantidad y distribución semanal (W1, W2, W3 según la duración)
3. La suma de las semanas debe ser igual a la cantidad total

`[📸 Captura: Editor de actividades para un programa recién creado, mostrando la tabla con columnas de semanas]`

**Paso 3 — Guardar cambios:**

Al final de la página se encuentra el botón **"Save All Changes"** con un banner azul explicativo. Este botón persiste **todos** los cambios (programas, actividades, recursos) al archivo de datos.

`[📸 Captura: Banner azul de "Persist All Changes" y botón "Save All Changes" al final de la página]`

> **Importante:** El botón "Create Program" solo registra el programa en la sesión. Los cambios no se guardan permanentemente hasta que haga clic en **"Save All Changes"**.

#### Eliminar un Programa

1. En **"Edit Existing Program"**, seleccione el programa a eliminar
2. Haga clic en **"Delete Program"**
3. Confirme la eliminación
4. Persista los cambios con **"Save All Changes"**

---

## 9. Flujos de Trabajo Recomendados

### 9.1 Verificación Diaria de Admisión (uso más frecuente)

```
1. Abrir la aplicación
   ↓
2. Ir a "Patients" → actualizar los pacientes actuales por programa y semana
   ↓
3. Ir a "Resources" → revisar que no haya recursos excedidos
   ↓
4. Ir a "Verify Admission" → agregar los pacientes que se desea admitir
   ↓
5. Hacer clic en "Verify Feasibility"
   ↓
6. Si es FACTIBLE → proceder con la admisión
   Si NO es FACTIBLE → revisar qué recursos limitan y ajustar
```

### 9.2 Consulta de Capacidad General

```
1. Abrir la aplicación
   ↓
2. Ir a "Patients" → registrar pacientes actuales
   ↓
3. Ir a "Resources" → consultar el porcentaje de uso de cada recurso
```

### 9.3 Agregar un Programa Nuevo (Administrador)

```
1. Iniciar sesión como administrador
   ↓
2. Ir a "Administration" → "Programs" → "Create New Program"
   ↓
3. Seguir los 3 pasos del banner informativo:
   a. Crear el programa (botón azul "Create Program")
   b. Agregar actividades con distribución semanal
   c. Guardar con "Save All Changes"
```

---

## 10. Preguntas Frecuentes

**¿Qué significan las columnas W1, W2, W3?**
Representan la semana de estancia del paciente en su programa. W1 = primera semana, W2 = segunda semana, W3 = tercera semana. El número de columnas depende de la duración del programa.

**¿Los datos de pacientes se guardan al cerrar el navegador?**
No. Los datos de pacientes ingresados en la pestaña "Patients" viven en la sesión del navegador y se pierden al cerrar. Los datos administrativos (programas, actividades, recursos) sí se guardan permanentemente al usar "Save All Changes".

**¿Cuál es la diferencia entre "Verify Admission" y "Optimization Results"?**
"Verify Admission" calcula con el consumo **real por semana** de cada paciente y es la herramienta recomendada para decisiones diarias. "Optimization Results" usa **promedios semanales** y sirve como referencia complementaria.

**¿Por qué un programa tiene 2 semanas si dura 8 días?**
La aplicación redondea hacia arriba: cualquier día adicional a una semana completa cuenta como una semana más. Así, 8 días = 2 semanas, 15 días = 3 semanas.

**¿Qué pasa si un recurso aparece como "Exceeded"?**
Significa que la demanda actual de pacientes supera la capacidad disponible de ese recurso. Revise si es necesario redistribuir pacientes o aumentar la capacidad del recurso desde Administration.

**¿Los nuevos pacientes siempre ingresan en semana 1?**
Sí. Al verificar admisión, el sistema asume que los nuevos pacientes comenzarán en la primera semana de su programa, que es cuando se consume el mayor volumen de actividades iniciales.

---

*Documento generado por Arkode — Marzo 2026*

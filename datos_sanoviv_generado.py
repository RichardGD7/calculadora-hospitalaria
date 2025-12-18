# -*- coding: utf-8 -*-

# Programas y pacientes actuales
orden_programas = [
    "Cancer Treatment",
    "Lyme Dase & Co-Infections",
    "Detox and Rejuvenation",
    "Stem Cell Rejuvenation",
    "NeuroFeedback Detox",
    "Medical Treatment",
    "Integrative Physical",
    "Long COVID Treatment",
    "Neuro Cognitive",
    "Mycotoxin Detox",
    "Microbiome Restore",
]

# Definición de Prioridades de los Programas
# Valores más altos = más prioridad. Si no defines esta lista, el modelo usa 1.0 para todos.
prioridad_programas = [
    6.90,  # Cancer Treatment
    7.13,  # Lyme Dase & Co-Infections
    8.91,  # Detox and Rejuvenation
    6.44,  # Stem Cell Rejuvenation
    2.84,  # NeuroFeedback Detox
    7.30,  # Medical Treatment
    8.85,  # Integrative Physical
    4.76,  # Long COVID Treatment
    4.25,  # Neuro Cognitive
    4.44,  # Mycotoxin Detox
    3.52,  # Microbiome Restore
]

# pacientes_actuales = [13, 9, 3, 0, 0, 9, 7, 0, 1, 0, 0]
# pacientes_actuales = [12, 8, 0, 2, 0, 2, 2, 0, 0, 0, 0]
# pacientes_actuales = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# pacientes_actuales = [5, 8, 0, 2, 0, 2, 2, 0, 0, 0, 0]
pacientes_actuales = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


# Recursos profesionales y físicos
nom_rec_prof = [
    "Asistente Dental",
    "Dentista",
    "Enfermero - Hipertermia",
    "Enfermero - Quirófano",
    "Enfermero general",
    "Fisico Terapeuta",
    "Fisico Terapeuta SPA",
    "Higienista Dental",
    "Instructor de Fitness",
    "Médico Oncólogo (y Cirujano)",
    "Médico de guardia",
    "Médico especialísta",
    "Medico Tratante",
    "Mind and Body Therapist",
    "Nutriólogo",
    "Psicólogo",
    "Quimico de Invest y Desarrollo",
    "Quiropráctico",
    "Radiólogo",
    "Técnico de Colonicos",
    "Técnico de Hiperbárica / Enfermera",
    "Técnico Radiologo",
    "Terapísta de Neurofeedback",
]
cap_rec_prof = [
    45.0,
    80.0,
    85.0,
    42.5,
    300.0,
    87.5,
    159.0,
    45.0,
    75.0,
    37.5,
    109.0,
    37.5,
    187.5,
    75.0,
    117.6,
    112.5,
    89.0,
    82.5,
    35.0,
    40.0,
    132.5,
    40.0,
    40.0,
]

nom_rec_fis = [
    "Cama de Enfermería recuperacion hipertermia",
    "Cama de Quiet Room",
    "Cámara de Hiperbárica",
    "Cámara de Hipertermia cuerpo completo",
    "Cámara de Hipertermia regional",
    "Consultorio de Fitness",
    "Consultorio de Hidroterapia de Colon",
    "Consultorio de MBT",
    "Consultorio de Nutrición",
    "Consultorio de Psicología",
    "Consultorio de Quiropráxia",
    "Consultorio Médico",
    "CT Scan",
    "Cuarto de flebotomía",
    "Cuarto de Hospitalización",
    "Cuarto de ozono",
    "Cuarto de Radiología",
    "Dormitorio",
    "Espacio de Comedor",
    "Gabinetes de Spa para Hombres",
    "Gabinetes de Spa para Mujeres",
    "Gastroenterología",
    "Maquina de ozono",
    "Módulo de Neuro Feedback",
    "Quirófano",
    "Rayos X Dental - Vatech",
    "Reposet (infusion centers)",
    "Resonancia",
    "Sala de masaje de SPA",
    "Sauna",
    "Termógrafo",
    "Ultrasonido",
    "Unidad Dental de Evaluación",
    "Unidad Dental de Tratamiento",
]
cap_rec_fis = [
    36.0,
    294.0,
    126.0,
    135.0,
    40.0,
    70.0,
    90.0,
    70.0,
    40.0,
    75.0,
    70.0,
    150.0,
    37.5,
    12.0,
    493.5,
    56.0,
    37.5,
    6552.0,
    1134.0,
    182.0,
    273.0,
    37.5,
    56.0,
    105.0,
    32.5,
    45.0,
    1288.0,
    37.5,
    315.0,
    126.0,
    37.5,
    130.0,
    90.0,
    135.0,
]

nom_rec_total = nom_rec_prof + nom_rec_fis
cap_rec_total = cap_rec_prof + cap_rec_fis

# Matriz de consumo de recursos profesionales
matriz_consumo_prof = [
    [
        0.58,
        0.88,
        1.5,
        1.75,
        1.75,
        0.88,
        1.75,
        0.88,
        0.88,
        1.13,
        1.25,
    ],  # Asistente Dental (1)
    [0.5, 0.75, 1.5, 1.5, 1.5, 0.75, 1.5, 0.75, 0.75, 1.0, 1.0],  # Dentista (2)
    [
        7.0,
        4.3,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        2.0,
        2.0,
        2.0,
        0.0,
    ],  # Enfermero - Hipertermia (2)
    [
        0.83,
        0.25,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.25,
        0.0,
    ],  # Enfermero - Quirófano (1)
    [
        10.17,
        14.71,
        0.25,
        7.17,
        0.25,
        6.13,
        2.33,
        8.42,
        11.38,
        6.04,
        4.92,
    ],  # Enfermero general (6)
    [
        6.17,
        3.25,
        6.5,
        8.5,
        6.5,
        3.25,
        0.5,
        3.75,
        3.25,
        3.25,
        0.5,
    ],  # Fisico Terapeuta (2)
    [
        4.17,
        3.0,
        8.5,
        4.5,
        7.0,
        3.75,
        1.0,
        4.75,
        4.75,
        6.0,
        2.5,
    ],  # Fisico Terapeuta SPA (4)
    [0.33, 0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.5, 0.0],  # Higienista Dental (1)
    [
        1.17,
        1.0,
        2.0,
        2.0,
        2.0,
        1.25,
        1.5,
        1.75,
        1.75,
        1.25,
        1.0,
    ],  # Instructor de Fitness (2)
    [
        0.83,
        0.25,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.25,
        0.0,
    ],  # Médico Oncólogo (y Cirujano) (1)
    [
        0.17,
        0.25,
        0.5,
        0.5,
        0.5,
        0.25,
        0.5,
        0.25,
        0.25,
        0.25,
        0.5,
    ],  # Médico de guardia (3)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 1.0, 2.38, 0.0, 2.0],  # Médico especialísta (1)
    [2.67, 3.0, 2.5, 2.5, 2.5, 3.0, 2.5, 3.25, 3.0, 2.5, 2.5],  # Medico Tratante (5)
    [
        2.5,
        1.75,
        1.5,
        1.5,
        1.5,
        2.25,
        1.0,
        1.75,
        1.75,
        1.75,
        1.0,
    ],  # Mind and Body Therapist (2)
    [
        1.83,
        1.88,
        2.25,
        2.25,
        1.75,
        1.88,
        1.75,
        1.88,
        1.63,
        1.38,
        2.25,
    ],  # Nutriólogo (3)
    [2.83, 2.75, 1.5, 1.5, 1.5, 2.75, 1.5, 2.75, 2.75, 2.25, 1.0],  # Psicólogo (3)
    [
        0.06,
        0.08,
        0.17,
        0.17,
        0.17,
        0.08,
        0.17,
        0.08,
        0.08,
        0.08,
        0.17,
    ],  # Quimico de Invest y Desarrollo (2)
    [1.0, 1.5, 1.5, 2.0, 1.5, 1.75, 1.5, 1.5, 1.5, 1.25, 1.0],  # Quiropráctico (2)
    [0.25, 0.38, 0.75, 1.25, 0.75, 0.63, 2.25, 0.38, 0.63, 0.38, 0.0],  # Radiólogo (1)
    [2.0, 2.0, 2.0, 1.0, 2.0, 2.0, 0.0, 1.5, 1.5, 1.0, 1.0],  # Técnico de Colonicos (1)
    [
        6.0,
        3.0,
        0.0,
        7.5,
        0.0,
        0.0,
        0.0,
        6.75,
        7.5,
        4.5,
        0.0,
    ],  # Técnico de Hiperbárica / Enfermera (1)
    [
        0.33,
        0.13,
        0.25,
        0.58,
        0.25,
        0.38,
        2.75,
        0.38,
        0.13,
        0.13,
        0.0,
    ],  # Técnico Radiologo (1)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        17.0,
        0.0,
        0.0,
        0.0,
        5.5,
        0.0,
        0.0,
    ],  # Terapísta de Neurofeedback (1)
]

# Matriz de consumo de recursos físicos
matriz_consumo_fis = [
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Cama de Enfermería recuperacion hipertermia (2)
    [
        6.17,
        3.25,
        6.5,
        8.5,
        6.5,
        3.25,
        0.5,
        3.75,
        3.25,
        3.25,
        0.5,
    ],  # Cama de Quiet Room (7)
    [
        6.0,
        3.0,
        0.0,
        7.5,
        0.0,
        0.0,
        0.0,
        6.75,
        7.5,
        4.5,
        0.0,
    ],  # Cámara de Hiperbárica (2)
    [
        4.0,
        4.3,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        2.0,
        2.0,
        2.0,
        0.0,
    ],  # Cámara de Hipertermia cuerpo completo (3)
    [
        3.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Cámara de Hipertermia regional (1)
    [
        1.17,
        1.0,
        2.0,
        2.0,
        2.0,
        1.25,
        1.5,
        1.75,
        1.75,
        1.25,
        1.0,
    ],  # Consultorio de Fitness (2)
    [
        2.0,
        2.0,
        2.0,
        1.0,
        2.0,
        2.0,
        0.0,
        1.5,
        1.5,
        1.0,
        1.0,
    ],  # Consultorio de Hidroterapia de Colon (2)
    [
        2.5,
        1.75,
        1.5,
        1.5,
        1.5,
        2.25,
        1.0,
        1.75,
        1.75,
        1.75,
        1.0,
    ],  # Consultorio de MBT (2)
    [
        0.5,
        0.63,
        1.25,
        1.25,
        1.25,
        0.63,
        1.25,
        0.63,
        0.63,
        0.63,
        1.25,
    ],  # Consultorio de Nutrición (1)
    [
        2.83,
        2.75,
        1.5,
        1.5,
        1.5,
        2.75,
        1.5,
        2.75,
        2.75,
        2.25,
        1.0,
    ],  # Consultorio de Psicología (2)
    [
        1.0,
        1.5,
        1.5,
        2.0,
        1.5,
        1.75,
        1.5,
        1.5,
        1.5,
        1.25,
        1.0,
    ],  # Consultorio de Quiropráxia (2)
    [
        2.83,
        3.25,
        3.0,
        3.0,
        3.0,
        3.25,
        4.0,
        4.5,
        4.13,
        2.75,
        3.0,
    ],  # Consultorio Médico (5)
    [0.17, 0.0, 0.0, 0.0, 0.0, 0.25, 2.0, 0.25, 0.0, 0.0, 0.0],  # CT Scan (1)
    [
        0.06,
        0.08,
        0.17,
        0.17,
        0.17,
        0.08,
        0.17,
        0.08,
        0.08,
        0.08,
        0.17,
    ],  # Cuarto de flebotomía (2)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Cuarto de Hospitalización (3)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 1.29, 1.17, 0.0, 0.67],  # Cuarto de ozono (1)
    [
        0.25,
        0.25,
        0.25,
        0.83,
        0.5,
        0.25,
        0.5,
        0.25,
        0.25,
        0.25,
        0.25,
    ],  # Cuarto de Radiología (1)
    [
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        96.0,
        168.0,
        168.0,
        168.0,
        120.0,
    ],  # Dormitorio (39)
    [
        21.0,
        21.0,
        21.0,
        21.0,
        21.0,
        21.0,
        12.0,
        21.0,
        21.0,
        21.0,
        15.0,
    ],  # Espacio de Comedor (54)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Gabinetes de Spa para Hombres (2)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Gabinetes de Spa para Mujeres (3)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 2.0],  # Gastroenterología (1)
    [0.0, 2.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],  # Maquina de ozono (1)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        17.0,
        0.0,
        0.0,
        0.0,
        5.5,
        0.0,
        0.0,
    ],  # Módulo de Neuro Feedback (3)
    [0.83, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0],  # Quirófano (1)
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ],  # Rayos X Dental - Vatech (1)
    [
        10.08,
        12.58,
        0.0,
        6.92,
        0.0,
        5.5,
        1.83,
        7.0,
        10.08,
        5.92,
        4.0,
    ],  # Reposet (infusion centers) (8)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Resonancia (1)
    [
        4.17,
        3.0,
        8.0,
        4.0,
        6.5,
        3.5,
        1.0,
        4.5,
        4.5,
        5.75,
        2.0,
    ],  # Sala de masaje de SPA (5)
    [0.0, 0.0, 6.0, 0.0, 6.0, 6.0, 0.0, 0.0, 5.0, 5.0, 0.0],  # Sauna (2)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0],  # Termógrafo (1)
    [
        0.25,
        0.38,
        0.75,
        1.25,
        0.75,
        0.63,
        2.25,
        0.38,
        0.63,
        0.38,
        0.0,
    ],  # Ultrasonido (4)
    [
        0.5,
        0.75,
        1.5,
        1.5,
        1.5,
        0.75,
        1.5,
        0.75,
        0.75,
        0.5,
        1.0,
    ],  # Unidad Dental de Evaluación (2)
    [
        0.33,
        0.5,
        0.0,
        0.0,
        0.0,
        0.5,
        0.0,
        0.5,
        0.5,
        1.0,
        0.0,
    ],  # Unidad Dental de Tratamiento (3)
]

# Sumatoria de Matriz de consumos Profesionales y Físicos
matriz_consumo_total = matriz_consumo_prof + matriz_consumo_fis

# Parámetros generales
NO_PROGRAMAS = len(orden_programas)
NO_RECURSOS = len(cap_rec_total)

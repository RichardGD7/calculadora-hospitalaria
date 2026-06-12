"""Capa de persistencia temporal (Supabase) para los datos editables del admin.

PARCHE TEMPORAL — atornillado por fuera mientras la app vive en Streamlit
Community Cloud (filesystem efímero). Cuando la app migre a un host con disco
persistente, este módulo se puede eliminar y la app vuelve a depender únicamente
de BD_sanoviv.py + guardar_datos_sanoviv() (reescritura de archivo).

Arquitectura "semilla + overrides":
  - BD_sanoviv.py sigue siendo la fuente de VALORES POR DEFECTO (semilla).
  - Supabase guarda un único documento JSON con los datos editados por el admin.
  - Al arrancar, la app carga el override (si existe) y lo aplica en memoria
    sobre el módulo de datos. Si Supabase no responde, se usan los defaults
    (a prueba de caídas: la app nunca se rompe por esto).

Tabla esperada en Supabase (crear una sola vez, ver instructivo):
    create table app_config (
        id          int primary key,
        data        jsonb not null,
        updated_at  timestamptz default now()
    );
"""

import streamlit as st
import requests

TABLA = "app_config"
_TIMEOUT = 10


def _creds():
    """Lee SUPABASE_URL y SUPABASE_KEY de st.secrets. (None, None) si faltan."""
    try:
        url = st.secrets["SUPABASE_URL"].rstrip("/")
        key = st.secrets["SUPABASE_KEY"]
        return url, key
    except Exception:
        return None, None


def esta_configurado() -> bool:
    """True si hay credenciales de Supabase en los secrets."""
    url, key = _creds()
    return bool(url and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def cargar_overrides():
    """Devuelve el documento JSON guardado (dict) o None.

    None significa: no configurado, sin datos guardados, o error de red.
    En todos esos casos la app debe usar los defaults de BD_sanoviv.py.
    """
    url, key = _creds()
    if not url:
        return None
    try:
        resp = requests.get(
            f"{url}/rest/v1/{TABLA}",
            params={"id": "eq.1", "select": "data"},
            headers=_headers(key),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        rows = resp.json()
        if rows and rows[0].get("data"):
            return rows[0]["data"]
        return None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def cargar_overrides_cached():
    """Versión cacheada (TTL 5 min) para no pegarle a la red en cada rerun.

    Compartida entre sesiones del mismo proceso. Se invalida con limpiar_cache()
    inmediatamente después de un guardado del admin.
    """
    return cargar_overrides()


def limpiar_cache():
    """Invalida el cache para que el próximo rerun relea desde Supabase."""
    try:
        cargar_overrides_cached.clear()
    except Exception:
        pass


def guardar_overrides(data: dict) -> bool:
    """Upsert del documento JSON (id=1) en Supabase. True si tuvo éxito."""
    url, key = _creds()
    if not url:
        return False
    try:
        resp = requests.post(
            f"{url}/rest/v1/{TABLA}",
            params={"on_conflict": "id"},
            headers={
                **_headers(key),
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
            json=[{"id": 1, "data": data}],
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception:
        return False


def diagnostico() -> dict:
    """Prueba la conexión en vivo y devuelve detalles para depurar.

    No se traga el error: reporta código HTTP / mensaje de Supabase para
    identificar exactamente qué está mal en las credenciales o la tabla.
    """
    url, key = _creds()
    out = {
        "configurado": esta_configurado(),
        "url_presente": bool(url),
        "key_presente": bool(key),
        "url_host": (url.split("//")[-1] if url else "(falta)"),
        "key_prefijo": (key[:8] + "…" if key else "(falta)"),
        "key_tipo": _adivinar_tipo_key(key),
    }
    if not (url and key):
        out["resultado"] = "ERROR: faltan SUPABASE_URL y/o SUPABASE_KEY en los secrets."
        return out
    try:
        resp = requests.get(
            f"{url}/rest/v1/{TABLA}",
            params={"id": "eq.1", "select": "data"},
            headers=_headers(key),
            timeout=_TIMEOUT,
        )
        out["http_status"] = resp.status_code
        if resp.status_code == 200:
            out["resultado"] = "OK: conexión y tabla correctas."
            out["filas_existentes"] = len(resp.json())
        else:
            out["resultado"] = f"ERROR HTTP {resp.status_code}"
            out["detalle"] = resp.text[:500]
    except Exception as e:
        out["resultado"] = "ERROR de red/excepción"
        out["detalle"] = f"{type(e).__name__}: {e}"
    return out


def _adivinar_tipo_key(key) -> str:
    """Heurística para detectar si copiaron la key correcta."""
    if not key:
        return "(falta)"
    if key.startswith("sb_secret_"):
        return "secret key (nueva) — correcta"
    if key.startswith("sb_publishable_"):
        return "publishable (PÚBLICA) — INCORRECTA, usa la secret key"
    if key.startswith("eyJ"):
        return "JWT (anon o service_role) — verifica que sea service_role"
    return "formato desconocido"


def aplicar_a_modulo(datos, data: dict) -> None:
    """Sobreescribe en memoria los atributos del módulo de datos (BD_sanoviv)
    y recomputa los helpers derivados, replicando el final de BD_sanoviv.py.

    Como Python cachea los módulos, tanto app.py como optimizador_v2.py
    comparten el mismo objeto `datos`, así que ambos ven los valores nuevos.
    """
    datos.programas = data["programas"]
    datos.recursos_profesionales = data["recursos_profesionales"]
    datos.recursos_fisicos = data["recursos_fisicos"]
    datos.catalogo_actividades = data["catalogo_actividades"]

    # ── Helpers derivados (idéntico a BD_sanoviv.py:7573-7580) ──
    datos.cap_rec_prof = {r["nombre"]: r["cap_semanal_total"] for r in datos.recursos_profesionales}
    datos.cap_rec_fis = {r["nombre"]: r["cap_semanal_total"] for r in datos.recursos_fisicos}
    datos.nombres_programas = list(datos.programas.keys())
    datos.duraciones_dias = {k: v["duracion_dias"] for k, v in datos.programas.items()}
    datos.prioridades = {k: v["prioridad"] for k, v in datos.programas.items()}
    datos.catalogo_por_nombre = {a["nombre"]: a for a in datos.catalogo_actividades}

    # Revalida/auto-corrige cantidad_por_semana, igual que al importar el módulo.
    datos.validar_cantidades_por_semana()

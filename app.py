import os
import io
import json
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
from PIL import Image
from groq import Groq

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="SkillPath — Apuntes Inteligentes en Vivo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RUTAS PERSISTENTES ---
DIR_BASE = "cuadernos_data"
DIR_AUDIO_RAW = os.path.join(DIR_BASE, "grabaciones_originales")
DIR_PERFILES = os.path.join(DIR_BASE, "perfil_usuario")
FILE_DB = os.path.join(DIR_BASE, "cuadernos_db.json")

for d in [DIR_BASE, DIR_AUDIO_RAW, DIR_PERFILES]:
    os.makedirs(d, exist_ok=True)

MODELO_WHISPER = "whisper-large-v3"

# --- OBTENCION SEGURA DE API KEY GROQ ---
def obtener_api_key():
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.environ.get("GROQ_API_KEY", "")

API_KEY_GROQ = obtener_api_key()

def obtener_cliente_ia():
    if not API_KEY_GROQ:
        return None
    try:
        return Groq(api_key=API_KEY_GROQ)
    except Exception:
        return None

def estructurar_apuntes_groq(client, texto_transcrito, materia, titulo, borrador_previo=""):
    prompt_sys = (
        f"Eres la asistente académica de excelencia de la estudiante universitaria Francesca Fellay "
        f"en la materia '{materia}'. Tu tarea es redactar y organizar apuntes académicos de alto nivel "
        f"en español latinoamericano, usando una redacción clara, precisa y pedagógica."
    )
    prompt_user = f"""
    Título de la clase: {titulo if titulo.strip() else 'Clase Universitaria'}.

    BORRADOR ACTUAL DE LOS APUNTES:
    \"\"\"
    {borrador_previo if borrador_previo.strip() else 'Inicio de la clase.'}
    \"\"\"

    NUEVA TRANSCRIPCIÓN DE LO HABLADO EN CLASE:
    \"\"\"
    {texto_transcrito}
    \"\"\"

    INSTRUCCIONES DE ESTRUCTURACIÓN:
    1. Integra la nueva información al borrador actual de forma fluida y sin duplicar ideas.
    2. Redacta los apuntes organizados exactamente con esta estructura profesional:
       # 📌 Resumen Ejecutivo de la Clase
       ## 🎯 Objetivos y Temas Principales
       ## 📝 Desarrollo Detallado y Conceptos Clave (con viñetas claras, definiciones y conceptos clave en negrita)
       ## 💡 Ejemplos Prácticos y Casos Mencionados
       ## ⚠️ Tareas, Acuerdos y Puntos Críticos para Estudiar
    3. Asegura que todo esté en español latino.
    """
    
    try:
        modelos_disponibles = [m.id for m in client.models.list().data if "whisper" not in m.id.lower() and "guard" not in m.id.lower()]
    except Exception:
        modelos_disponibles = []

    modelos_fallback = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]

    candidatos = [m for m in modelos_fallback if m in modelos_disponibles] + modelos_disponibles + modelos_fallback
    candidatos = list(dict.fromkeys(candidatos))

    ultimo_error = None
    for m in candidatos:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": prompt_sys},
                    {"role": "user", "content": prompt_user}
                ],
                temperature=0.3
            )
            return resp.choices[0].message.content
        except Exception as e:
            ultimo_error = e
            continue

    raise Exception(f"Fallo al conectar con los modelos de Groq. Detalle: {ultimo_error}")

# --- ESTILOS VISUALES SKILLPATH: CONTRASTE MEJORADO ---
st.markdown("""
<style>
/* Fondo general lavanda-slate para contraste con tarjetas blancas */
html, body, [class*="css"], .stApp { 
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important; 
    background-color: #e9e5f5 !important;
    color: #1e1b4b !important;
}

.brand-navbar {
    background: linear-gradient(135deg, #6214c7 0%, #7c24ec 100%);
    padding: 16px 24px;
    border-radius: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #ffffff;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(109, 36, 236, 0.25);
}
.brand-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #ffffff !important;
}

/* BARRA LATERAL */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6214c7 0%, #4c1d95 100%) !important;
    border-right: 2px solid #3b0764 !important;
}
section[data-testid="stSidebar"] * {
    color: #f5f3ff !important;
    font-weight: 600;
}
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] h4 {
    color: #ffffff !important;
    font-weight: 800 !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    background-color: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
    background-color: rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ==========================================================================
   SOBREESCRITURA TOTAL DE PESTAÑAS (TABS)
   ========================================================================== */
[data-testid="stTabs"] {
    --primary-color: #6214c7 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 2.5px solid #c084fc !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #6214c7 !important;
    height: 3.5px !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    background-color: #c084fc !important;
}

/* Pestañas inactivas: fondo lavanda claro visible, texto morado */
[data-testid="stTabs"] button[role="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-testid="stTabs"] button {
    background-color: #ffffff !important;
    border: 1.5px solid #c4b5fd !important;
    border-bottom: none !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 10px 20px !important;
    box-shadow: 0 2px 6px rgba(109, 36, 236, 0.06) !important;
    opacity: 1 !important;
}

[data-testid="stTabs"] button[role="tab"] *,
[data-testid="stTabs"] button[data-baseweb="tab"] *,
[data-testid="stTabs"] button p,
[data-testid="stTabs"] button span,
[data-testid="stTabs"] button div {
    color: #5b21b6 !important;
    -webkit-text-fill-color: #5b21b6 !important;
    font-weight: 800 !important;
    font-size: 1.02rem !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Pestaña seleccionada: fondo morado, texto blanco */
[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
div[data-testid="stTabs"] button[aria-selected="true"] {
    background-color: #6214c7 !important;
    border: 1.5px solid #6214c7 !important;
    border-bottom: none !important;
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] *,
[data-testid="stTabs"] button[aria-selected="true"] p,
[data-testid="stTabs"] button[aria-selected="true"] span,
[data-testid="stTabs"] button[aria-selected="true"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 900 !important;
    opacity: 1 !important;
}

[data-testid="stTabs"] button[role="tab"]:hover,
[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    background-color: #ede9fe !important;
}

/* DESPLEGABLES */
div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(109, 36, 236, 0.08) !important;
    margin-bottom: 16px !important;
}
div[data-testid="stExpander"] summary {
    background: linear-gradient(135deg, #7c3aed 0%, #6214c7 100%) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 750 !important;
    padding: 12px 18px !important;
}
div[data-testid="stExpander"] summary * {
    color: #ffffff !important;
    font-weight: 750 !important;
}

/* Inputs y Selectores */
input[type="text"], input[type="password"] {
    background-color: #ffffff !important;
    color: #1e1b4b !important;
    border: 1.5px solid #c084fc !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #faf5ff !important;
    border: 1.5px solid #c084fc !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    background-color: transparent !important;
    color: #1e1b4b !important;
    font-weight: 750 !important;
}

/* Botones */
.stButton>button, div[data-testid="stFormSubmitButton"]>button {
    background: linear-gradient(135deg, #7c3aed 0%, #6214c7 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 14px rgba(109, 36, 236, 0.25) !important;
}
.stButton>button p, div[data-testid="stFormSubmitButton"]>button p {
    color: #ffffff !important;
    font-weight: 800 !important;
}

div[data-testid="stDownloadButton"]>button {
    background: #ede9fe !important;
    color: #4c1d95 !important;
    border: 1.5px solid #c084fc !important;
    border-radius: 9px !important;
    padding: 8px 18px !important;
    font-weight: 750 !important;
}

/* GRABADOR DE AUDIO NATIVO */
div[data-testid="stAudioInput"] {
    background-color: #ffffff !important;
    border: 2px dashed #8b5cf6 !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
div[data-testid="stAudioInput"] * {
    color: #3b0764 !important;
    font-weight: 750 !important;
}

.welcome-card {
    background: linear-gradient(135deg, #6d28d9 0%, #8b5cf6 100%);
    color: white;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 6px 20px rgba(109, 40, 217, 0.25);
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.stat-card-1 { background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); color: white; border-radius: 14px; padding: 18px; }
.stat-card-2 { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); color: white; border-radius: 14px; padding: 18px; }
.stat-card-3 { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border-radius: 14px; padding: 18px; }
.stat-card-4 { background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: white; border-radius: 14px; padding: 18px; }
.stat-value { font-size: 1.8rem; font-weight: 800; margin: 0; line-height: 1.2; }
.stat-label { font-size: 0.85rem; font-weight: 600; opacity: 0.9; }

.app-card {
    background: #ffffff;
    border: 1px solid #d8b4fe;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 14px rgba(109, 36, 236, 0.06);
}

.live-notes-box {
    background-color: #ffffff;
    border: 2px solid #8b5cf6;
    border-radius: 14px;
    padding: 22px;
    min-height: 280px;
    max-height: 520px;
    overflow-y: auto;
    font-size: 0.96rem;
    color: #1e1b4b;
    line-height: 1.6;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.1);
    margin-top: 10px;
    scrollbar-color: #8b5cf6 #ede9fe;
    scrollbar-width: thin;
}

.live-notes-box::-webkit-scrollbar {
    width: 10px;
}
.live-notes-box::-webkit-scrollbar-track {
    background: #ede9fe;
    border-radius: 8px;
}
.live-notes-box::-webkit-scrollbar-thumb {
    background: #8b5cf6;
    border-radius: 8px;
    border: 2px solid #ede9fe;
}
.live-notes-box::-webkit-scrollbar-thumb:hover {
    background: #6214c7;
}

/* PANTALLA DE ACCESO */
.login-container {
    background: #ffffff;
    border: 2px solid #c084fc;
    border-radius: 18px;
    padding: 38px 34px;
    box-shadow: 0 12px 32px rgba(109, 36, 236, 0.15);
    margin-top: 50px;
}
</style>
""", unsafe_allow_html=True)

# --- USUARIOS PERMITIDOS ---
USUARIOS_ACCESO = {
    "Francesca Fellay": "1953",
    "gerente": "gerente"
}

# --- CONTROL DE ACCESO (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_activo = None

if not st.session_state.autenticado:
    c_izq, c_cen, c_der = st.columns([1, 1.3, 1])
    with c_cen:
        st.markdown("""
        <div class='login-container'>
            <div style='text-align: center; margin-bottom: 22px;'>
                <div style='font-size: 3.2rem; margin-bottom: 4px;'>⚡</div>
                <h2 style='margin: 0; color: #4c1d95 !important; font-size: 1.9rem;'>SkillPath</h2>
                <p style='margin: 4px 0 0 0; color: #64748b; font-size: 0.95rem; font-weight: 600;'>Plataforma de Apuntes Inteligentes en Vivo</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_acceso_skillpath"):
            st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:4px;'>Nombre de Usuario:</p>", unsafe_allow_html=True)
            usr_input = st.text_input("Usuario", label_visibility="collapsed")
            
            st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:4px; margin-top:12px;'>PIN / Contraseña:</p>", unsafe_allow_html=True)
            pin_input = st.text_input("PIN", type="password", label_visibility="collapsed")
            
            st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("Ingresar a la Plataforma", use_container_width=True)
            
            if submit_btn:
                usr_clean = usr_input.strip()
                if usr_clean in USUARIOS_ACCESO and USUARIOS_ACCESO[usr_clean] == pin_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = usr_clean
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique el usuario y el PIN ingresado.")
                    
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- GESTOR DE PERSISTENCIA Y RECUPERACION ANTI-HIBERNACION ---
def sincronizar_y_recuperar_todo(data):
    rutas_db = {g.get("ruta") for g in data.get("grabaciones", []) if g.get("ruta")}
    if os.path.exists(DIR_AUDIO_RAW):
        for arch in os.listdir(DIR_AUDIO_RAW):
            ruta_f = os.path.join(DIR_AUDIO_RAW, arch)
            if ruta_f not in rutas_db and os.path.isfile(ruta_f):
                partes = arch.split("_", 2)
                mat_nombre = partes[2].rsplit(".", 1)[0] if len(partes) > 2 else "Materia General"
                data["grabaciones"].append({
                    "titulo": f"Grabación ({arch})",
                    "materia": mat_nombre,
                    "modulo": "6to Semestre TSL",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "ruta": ruta_f
                })
    return data

def cargar_estado():
    data_inicial = {
        "perfil": {
            "nombre": "Francesca Fellay",
            "universidad": "Pontificia Universidad Católica de Valparaíso",
            "ubicacion": "Valparaíso, Chile",
            "avatar": ""
        },
        "modulos": {
            "6to Semestre TSL": {
                "carpetas": {}
            }
        },
        "grabaciones": []
    }
    
    if not os.path.exists(FILE_DB):
        data = sincronizar_y_recuperar_todo(data_inicial)
        guardar_estado(data)
        return data
    
    with open(FILE_DB, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = data_inicial
    
    if "modulos" not in data:
        data["modulos"] = data_inicial["modulos"]
    if "grabaciones" not in data:
        data["grabaciones"] = []
        
    data = sincronizar_y_recuperar_todo(data)
    guardar_estado(data)
    return data

def guardar_estado(data):
    with open(FILE_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = cargar_estado()

# --- BARRA LATERAL ---
st.sidebar.markdown("### 🎓 Mi Perfil Académico")
perfil = db.get("perfil", {})
avatar_path = perfil.get("avatar", "")

if avatar_path and os.path.exists(avatar_path):
    st.sidebar.image(avatar_path, width=110)
else:
    st.sidebar.markdown("""
        <div style='width:90px; height:90px; border-radius:50%; background:linear-gradient(135deg, #a78bfa, #ede9fe); display:flex; align-items:center; justify-content:center; font-size:2.4rem; margin-bottom:12px; border:2px solid #ffffff;'>
            👩‍🎓
        </div>
    """, unsafe_allow_html=True)

nombre_mostrado = perfil.get('nombre', 'Francesca Fellay') if st.session_state.usuario_activo == "Francesca Fellay" else "Gerencia General"
st.sidebar.markdown(f"<h3 style='margin:0; font-size:1.15rem; color:#ffffff;'>{nombre_mostrado}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='margin:2px 0; font-size:0.85rem; color:#ede9fe;'>🏛️ {perfil.get('universidad', 'Pontificia Universidad Católica de Valparaíso')}</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='margin:2px 0 10px 0; font-size:0.85rem; color:#ede9fe;'>📍 {perfil.get('ubicacion', 'Valparaíso, Chile')}</p>", unsafe_allow_html=True)

with st.sidebar.expander("⚙️ Editar Datos del Perfil"):
    n_nom = st.text_input("Nombre:", value=perfil.get("nombre", "Francesca Fellay"))
    n_uni = st.text_input("Universidad:", value=perfil.get("universidad", "Pontificia Universidad Católica de Valparaíso"))
    n_ubi = st.text_input("Ubicación:", value=perfil.get("ubicacion", "Valparaíso, Chile"))
    n_img = st.file_uploader("Foto de perfil (JPG/PNG):", type=["jpg", "jpeg", "png"])
    
    if st.button("Guardar Perfil"):
        db["perfil"]["nombre"] = n_nom
        db["perfil"]["universidad"] = n_uni
        db["perfil"]["ubicacion"] = n_ubi
        if n_img is not None:
            r_av = os.path.join(DIR_PERFILES, "avatar_usuario.png")
            with open(r_av, "wb") as f_av:
                f_av.write(n_img.getbuffer())
            db["perfil"]["avatar"] = r_av
        guardar_estado(db)
        st.success("Perfil actualizado.")
        st.rerun()

st.sidebar.markdown("<hr style='border:0.5px solid rgba(255,255,255,0.2); margin:16px 0;'>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_activo = None
    st.rerun()

# --- SELECTOR DE MÓDULO ---
st.sidebar.markdown("### 📚 Selector de Módulo")
lista_modulos = list(db["modulos"].keys())
if not lista_modulos:
    db["modulos"]["6to Semestre TSL"] = {"carpetas": {}}
    guardar_estado(db)
    lista_modulos = ["6to Semestre TSL"]

modulo_actual = st.sidebar.selectbox("Módulo Activo:", lista_modulos)

with st.sidebar.expander("➕ Crear Nuevo Módulo"):
    nuevo_mod_nom = st.text_input("Nombre del nuevo módulo:")
    if st.button("Crear Módulo"):
        if nuevo_mod_nom.strip() and nuevo_mod_nom not in db["modulos"]:
            db["modulos"][nuevo_mod_nom] = {"carpetas": {}}
            guardar_estado(db)
            st.success("Módulo creado con éxito.")
            st.rerun()

# --- HEADER BRAND ---
tz_cl = pytz.timezone("America/Santiago")
hora_actual = datetime.now(tz_cl).strftime("%d/%m/%Y | %H:%M:%S")

st.markdown(f"""
<div class='brand-navbar'>
    <div class='brand-title'>
        <span>⚡ SkillPath</span>
        <span style='font-size:0.9rem; font-weight:500; opacity:0.85;'>| Plataforma de Apuntes en Vivo & IA</span>
    </div>
    <div style='font-size:0.88rem; font-weight:600;'>🇨🇱 {hora_actual}</div>
</div>
""", unsafe_allow_html=True)

pestañas_principales = st.tabs(["📁 Mis Carpetas & Clases", "🎙️ Grabaciones Originales"])

# ==========================================
# 1. MIS CARPETAS & CLASES
# ==========================================
with pestañas_principales[0]:
    carpetas_modulo = db["modulos"][modulo_actual]["carpetas"]
    total_carpetas = len(carpetas_modulo)
    total_clases = sum(len(c.get("clases", [])) for c in carpetas_modulo.values())
    
    st.markdown(f"""
    <div class='welcome-card'>
        <h2 style='margin:0 0 6px 0;'>¡Bienvenida de vuelta, {nombre_mostrado}! 👋</h2>
        <p style='margin:0; opacity:0.9;'>Módulo actual: <b>{modulo_actual}</b>. Transcripción y viñetas automáticas en <b>Español Latino</b> con botones nativos.</p>
    </div>
    <div class='stats-grid'>
        <div class='stat-card-1'><div class='stat-value'>{total_carpetas}</div><div class='stat-label'>Materias / Carpetas</div></div>
        <div class='stat-card-2'><div class='stat-value'>{total_clases}</div><div class='stat-label'>Clases Procesadas</div></div>
        <div class='stat-card-3'><div class='stat-value'>{len(db['grabaciones'])}</div><div class='stat-label'>Audios Grabados</div></div>
        <div class='stat-card-4'><div class='stat-value'>⚡ En Vivo</div><div class='stat-label'>Botones Nativos</div></div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Crear Nueva Carpeta de Materia en " + modulo_actual, expanded=(total_carpetas == 0)):
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            nom_carpeta = st.text_input("Nombre de la Materia / Ramo:", placeholder="Ej. Taller de Intervención Social")
        with col_c2:
            desc_carpeta = st.text_input("Profesor / Descripción breve:")
        
        if st.button("Crear Carpeta de Materia"):
            if nom_carpeta.strip():
                if nom_carpeta not in carpetas_modulo:
                    carpetas_modulo[nom_carpeta] = {
                        "descripcion": desc_carpeta,
                        "fecha_creacion": datetime.now(tz_cl).strftime("%Y-%m-%d %H:%M"),
                        "clases": []
                    }
                    guardar_estado(db)
                    st.success(f"Carpeta '{nom_carpeta}' agregada al módulo.")
                    st.rerun()
                else:
                    st.error("Ya existe una carpeta con ese nombre en este módulo.")

    st.markdown("---")

    if not carpetas_modulo:
        st.info(f"Aún no has creado carpetas en el módulo '{modulo_actual}'. Crea la primera materia arriba.")
    else:
        lista_nombres_carpetas = list(carpetas_modulo.keys())
        tabs_carpetas = st.tabs([f"📂 {nom}" for nom in lista_nombres_carpetas])

        for idx_tab, tab_materia in enumerate(tabs_carpetas):
            nombre_mat = lista_nombres_carpetas[idx_tab]
            info_mat = carpetas_modulo[nombre_mat]

            with tab_materia:
                st.markdown(f"### 📖 {nombre_mat}")
                st.caption(f"Detalle: **{info_mat.get('descripcion', 'Sin descripción')}** | Creada: {info_mat.get('fecha_creacion')}")
                
                nom_sesion_live = st.text_input("Tema / Título de la clase:", placeholder="Ej. Clase 1: Diagnóstico Comunitario", key=f"t_live_input_{nombre_mat}")

                session_key_borrador = f"live_notes_draft_{modulo_actual}_{nombre_mat}"
                session_key_last_proc = f"last_processed_audio_sig_{modulo_actual}_{nombre_mat}"

                if session_key_borrador not in st.session_state:
                    st.session_state[session_key_borrador] = ""
                if session_key_last_proc not in st.session_state:
                    st.session_state[session_key_last_proc] = ""

                # --- CONTROL NATIVO OFICIAL DE STREAMLIT ---
                st.markdown("""
                <div class='app-card'>
                    <h4 style='margin:0 0 8px 0; color:#5b21b6;'>🎙️ Grabación en Vivo con Botones Nativos</h4>
                    <p style='color:#64748b; font-size:0.9rem; margin-bottom:12px;'>
                        Presiona el micrófono nativo para grabar. Cada vez que captures voz, la IA transcribirá y estructurará automáticamente los apuntes con viñetas y conceptos clave en español latino en el cuadro inferior.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                c_rec_live, c_up_live = st.columns([1.2, 1.2])
                with c_rec_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>Grabar con Micrófono Nativo:</p>", unsafe_allow_html=True)
                    audio_live_in = st.audio_input("Botones Oficiales (Grabar / Pausar / Detener):", key=f"live_audio_in_{modulo_actual}_{nombre_mat}")

                with c_up_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>O Cargar Archivo de Audio:</p>", unsafe_allow_html=True)
                    uploaded_live_in = st.file_uploader("Formatos (.wav, .mp3, .m4a):", type=["wav", "mp3", "m4a"], key=f"live_up_in_{modulo_actual}_{nombre_mat}")

                audio_bytes_capturados = None
                ext_capturado = "wav"

                if audio_live_in is not None:
                    audio_bytes_capturados = audio_live_in.getvalue()
                    ext_capturado = "wav"
                elif uploaded_live_in is not None:
                    audio_bytes_capturados = uploaded_live_in.getvalue()
                    ext_capturado = uploaded_live_in.name.split(".")[-1].lower()

                # --- PIPELINE REACTIVO CONTINUO ---
                if audio_bytes_capturados is not None:
                    audio_sig = f"{len(audio_bytes_capturados)}_{hash(audio_bytes_capturados[:64])}"
                    if audio_sig != st.session_state[session_key_last_proc]:
                        client = obtener_cliente_ia()
                        if not client:
                            st.error("⚠️ Clave GROQ_API_KEY no configurada en Secrets de Streamlit.")
                        else:
                            with st.spinner("⚡ Transcribiendo con Whisper y estructurando apuntes en vivo..."):
                                try:
                                    audio_buffer = io.BytesIO(audio_bytes_capturados)
                                    audio_buffer.name = f"audio_temp.{ext_capturado}"
                                    transcripcion = client.audio.transcriptions.create(
                                        model=MODELO_WHISPER,
                                        file=audio_buffer,
                                        language="es"
                                    )
                                    texto_transcrito = transcripcion.text

                                    apuntes_generados = estructurar_apuntes_groq(
                                        client=client,
                                        texto_transcrito=texto_transcrito,
                                        materia=nombre_mat,
                                        titulo=nom_sesion_live,
                                        borrador_previo=st.session_state[session_key_borrador]
                                    )

                                    st.session_state[session_key_borrador] = apuntes_generados
                                    st.session_state[session_key_last_proc] = audio_sig

                                    # Guardado en grabaciones originales
                                    n_aud_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nombre_mat}.{ext_capturado}"
                                    r_dest = os.path.join(DIR_AUDIO_RAW, n_aud_name)
                                    with open(r_dest, "wb") as f_raw:
                                        f_raw.write(audio_bytes_capturados)
                                    
                                    db["grabaciones"].append({
                                        "titulo": nom_sesion_live if nom_sesion_live.strip() else f"Grabación {datetime.now(tz_cl).strftime('%d/%m/%Y %H:%M')}",
                                        "materia": nombre_mat,
                                        "modulo": modulo_actual,
                                        "fecha": datetime.now(tz_cl).strftime("%Y-%m-%d %H:%M"),
                                        "ruta": r_dest
                                    })
                                    guardar_estado(db)
                                    st.success("✅ ¡Apuntes redactados y estructurados con éxito!")
                                except Exception as e:
                                    st.error(f"Error procesando con Groq: {e}")

                # --- CUADRO EN VIVO: APUNTES ESTRUCTURADOS ---
                st.markdown("##### 📝 Cuadro de Apuntes Estructurados en Vivo (Español Latino):")
                if st.session_state[session_key_borrador]:
                    st.markdown(f"<div class='live-notes-box'>{st.session_state[session_key_borrador]}</div>", unsafe_allow_html=True)

                    c_save1, c_save2 = st.columns([2, 1])
                    with c_save1:
                        if st.button("💾 Guardar Clase en Cuaderno Permanente", key=f"btn_save_perm_{nombre_mat}"):
                            titulo_final = nom_sesion_live.strip() if nom_sesion_live.strip() else f"Clase del {datetime.now(tz_cl).strftime('%d/%m/%Y %H:%M')}"
                            info_mat["clases"].append({
                                "id": f"clase_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "titulo": titulo_final,
                                "fecha": datetime.now(tz_cl).strftime("%d/%m/%Y %H:%M"),
                                "contenido": st.session_state[session_key_borrador],
                                "chat": []
                            })
                            guardar_estado(db)
                            st.session_state[session_key_borrador] = ""
                            st.session_state[session_key_last_proc] = ""
                            st.success("¡Clase archivada exitosamente en tu cuaderno permanente!")
                            st.rerun()

                    with c_save2:
                        if st.button("🔄 Reiniciar Borrador en Vivo", key=f"btn_reset_live_{nombre_mat}"):
                            st.session_state[session_key_borrador] = ""
                            st.session_state[session_key_last_proc] = ""
                            st.rerun()
                else:
                    st.markdown("""
                    <div class='live-notes-box' style='color:#94a3b8; font-style:italic;'>
                        Presiona el botón nativo del micrófono arriba para empezar a grabar. La IA redactará aquí tus apuntes organizados en viñetas, conceptos clave y explicaciones en español latino sobre la marcha...
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # --- HISTORIAL DE CLASES GUARDADAS EN LA MATERIA ---
                st.markdown("#### 📚 Cuaderno de Apuntes Guardados")
                clases_guardadas = info_mat.get("clases", [])
                
                if not clases_guardadas:
                    st.info("Aún no has archivado clases en esta materia. Graba con el botón de arriba para comenzar.")
                else:
                    for idx_c, clase in enumerate(reversed(clases_guardadas)):
                        idx_real = len(clases_guardadas) - 1 - idx_c
                        with st.expander(f"📝 {clase['titulo']} — ({clase['fecha']})", expanded=(idx_c == 0)):
                            c_hist_content, c_hist_actions = st.columns([4, 1])
                            with c_hist_content:
                                st.markdown(clase["contenido"])
                            
                            with c_hist_actions:
                                st.download_button(
                                    "📥 Descargar (.txt)",
                                    data=clase["contenido"],
                                    file_name=f"{clase['titulo']}_Apuntes.txt",
                                    key=f"dl_txt_{clase['id']}"
                                )
                                if st.button("🗑️ Eliminar Clase", key=f"del_cls_{clase['id']}"):
                                    clases_guardadas.pop(idx_real)
                                    guardar_estado(db)
                                    st.success("Clase eliminada.")
                                    st.rerun()

                            st.markdown("---")
                            
                            # Tutor Chat
                            st.markdown(f"##### 💬 Tutor IA: Consultas sobre '{clase['titulo']}'")
                            historial_chat = clase.get("chat", [])
                            for mensaje in historial_chat:
                                if mensaje["rol"] == "user":
                                    st.markdown(f"**Tú:** {mensaje['texto']}")
                                else:
                                    st.markdown(f"**🤖 Tutor IA:** {mensaje['texto']}")

                            with st.form(f"form_chat_{clase['id']}"):
                                pregunta_usuario = st.text_input("Haz una pregunta sobre el contenido de esta clase:", placeholder="Ej. ¿Qué autores se citaron?", key=f"inp_chat_{clase['id']}")
                                if st.form_submit_button("Consultar al Tutor") and pregunta_usuario.strip():
                                    client = obtener_cliente_ia()
                                    if client:
                                        with st.spinner("Pensando respuesta..."):
                                            p_sys = "Eres un tutor académico de apoyo para la estudiante Francesca Fellay. Responde siempre en español latinoamericano, de forma pedagógica, clara y directa."
                                            p_user = f"Contexto de los apuntes ({clase['titulo']}):\n{clase['contenido']}\n\nPregunta: {pregunta_usuario}"
                                            try:
                                                resp_tutor = estructurar_apuntes_groq(
                                                    client=client,
                                                    texto_transcrito=f"Pregunta del alumno: {pregunta_usuario}",
                                                    materia=nombre_mat,
                                                    titulo=clase['titulo'],
                                                    borrador_previo=clase['contenido']
                                                )
                                                if "chat" not in clases_guardadas[idx_real]:
                                                    clases_guardadas[idx_real]["chat"] = []
                                                
                                                clases_guardadas[idx_real]["chat"].append({"rol": "user", "texto": pregunta_usuario})
                                                clases_guardadas[idx_real]["chat"].append({"rol": "ai", "texto": resp_tutor})
                                                guardar_estado(db)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error en tutor: {e}")

# ==========================================
# 2. GRABACIONES ORIGINALES
# ==========================================
with pestañas_principales[1]:
    st.markdown("""
    <div class='app-card'>
        <h3 style='margin:0 0 6px 0; color:#5b21b6;'>🎙️ Repositorio Central de Grabaciones Originales</h3>
        <p style='margin:0; color:#64748b;'>Todas las grabaciones de voz se almacenan de forma segura aquí para su reproducción o descarga.</p>
    </div>
    """, unsafe_allow_html=True)

    grabaciones = db.get("grabaciones", [])
    if not grabaciones:
        st.info("No hay grabaciones de audio guardadas todavía.")
    else:
        for idx_g, g in enumerate(reversed(grabaciones)):
            idx_real_g = len(grabaciones) - 1 - idx_g
            with st.container():
                c_g1, c_g2 = st.columns([4, 1])
                with c_g1:
                    st.markdown(f"#### 🎵 {g['titulo']}")
                    st.caption(f"Materia: **{g['materia']}** | Módulo: **{g.get('modulo', 'General')}** | Grabado: {g['fecha']}")
                    if os.path.exists(g["ruta"]):
                        with open(g["ruta"], "rb") as f_play:
                            st.audio(f_play.read())
                    else:
                        st.error("Archivo físico no encontrado.")
                with c_g2:
                    if os.path.exists(g["ruta"]):
                        with open(g["ruta"], "rb") as f_dl:
                            st.download_button(
                                "📥 Descargar Audio",
                                data=f_dl.read(),
                                file_name=os.path.basename(g["ruta"]),
                                key=f"dl_raw_{idx_real_g}"
                            )
                    if st.button("🗑️ Eliminar Audio", key=f"del_raw_{idx_real_g}"):
                        if os.path.exists(g["ruta"]):
                            os.remove(g["ruta"])
                        grabaciones.pop(idx_real_g)
                        guardar_estado(db)
                        st.success("Grabación eliminada.")
                        st.rerun()
                st.markdown("---")

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
    os.makedirs(d, exist_ok=True)[cite: 6]

MODELO_WHISPER = "whisper-large-v3"[cite: 6]

# --- OBTENCION SEGURA DE API KEY GROQ ---
def obtener_api_key():
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"][cite: 6]
    return os.environ.get("GROQ_API_KEY", "")[cite: 6]

API_KEY_GROQ = obtener_api_key()[cite: 6]

def obtener_cliente_ia():
    if not API_KEY_GROQ:
        return None
    try:
        return Groq(api_key=API_KEY_GROQ)[cite: 6]
    except Exception as e:
        st.error(f"Error al conectar con Groq: {e}")
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
    
    # Obtener modelos activos reales de la cuenta
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

# --- ESTILOS VISUALES SKILLPATH (LAVANDA & MORADO) ---
st.markdown("""
<style>
html, body, [class*="css"], .stApp { 
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important; 
    background-color: #f4f5fa !important;
    color: #1e1b4b;
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
    background: linear-gradient(180deg, #6214c7 0%, #520eb0 100%) !important;
    border-right: 1.5px solid #450c96 !important;
}
section[data-testid="stSidebar"] * {
    color: #f5f3ff !important;
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

/* DESPLEGABLES */
div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(109, 36, 236, 0.1) !important;
    margin-bottom: 16px !important;
}
div[data-testid="stExpander"] summary {
    background: linear-gradient(135deg, #7c24ec 0%, #6214c7 100%) !important;
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
section[data-testid="stSidebar"] input[type="text"] {
    background-color: #ede9fe !important;
    color: #2e1065 !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #ede9fe !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    background-color: transparent !important;
    color: #2e1065 !important;
    font-weight: 750 !important;
}

/* Botones */
.stButton>button {
    background: linear-gradient(135deg, #6214c7 0%, #7c24ec 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 9px 22px !important;
    font-weight: 750 !important;
}

div[data-testid="stDownloadButton"]>button {
    background: #ede9fe !important;
    color: #4c1d95 !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 9px !important;
    padding: 8px 18px !important;
    font-weight: 750 !important;
}

/* GRABADOR DE AUDIO NATIVO */
div[data-testid="stAudioInput"] {
    background-color: #ede9fe !important;
    border: 2px dashed #8b5cf6 !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
div[data-testid="stAudioInput"] * {
    color: #3b0764 !important;
    font-weight: 750 !important;
}

.welcome-card {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.2);
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
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
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
}
</style>
""", unsafe_allow_html=True)[cite: 6]

# --- GESTOR DE PERSISTENCIA ---
def cargar_estado():
    if not os.path.exists(FILE_DB):
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
        guardar_estado(data_inicial)
        return data_inicial
    
    with open(FILE_DB, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = {"perfil": {"nombre": "Francesca Fellay", "universidad": "Pontificia Universidad Católica de Valparaíso", "ubicacion": "Valparaíso, Chile", "avatar": ""}, "modulos": {"6to Semestre TSL": {"carpetas": {}}}, "grabaciones": []}
    
    if "modulos" in data:
        if "6to semestre TSL" in data["modulos"]:
            contenido_viejo = data["modulos"].pop("6to semestre TSL")
            if "6to Semestre TSL" not in data["modulos"]:
                data["modulos"]["6to Semestre TSL"] = contenido_viejo
            guardar_estado(data)
    else:
        data["modulos"] = {"6to Semestre TSL": {"carpetas": {}}}
        guardar_estado(data)
        
    return data[cite: 6]

def guardar_estado(data):
    with open(FILE_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)[cite: 6]

db = cargar_estado()[cite: 6]

# --- BARRA LATERAL ---
st.sidebar.markdown("### 🎓 Mi Perfil Académico")[cite: 6]
perfil = db.get("perfil", {})[cite: 6]
avatar_path = perfil.get("avatar", "")[cite: 6]

if avatar_path and os.path.exists(avatar_path):
    st.sidebar.image(avatar_path, width=110)[cite: 6]
else:
    st.sidebar.markdown("""
        <div style='width:90px; height:90px; border-radius:50%; background:linear-gradient(135deg, #a78bfa, #ede9fe); display:flex; align-items:center; justify-content:center; font-size:2.4rem; margin-bottom:12px; border:2px solid #ffffff;'>
            👩‍🎓
        </div>
    """, unsafe_allow_html=True)[cite: 6]

st.sidebar.markdown(f"<h3 style='margin:0; font-size:1.15rem; color:#ffffff;'>{perfil.get('nombre', 'Francesca Fellay')}</h3>", unsafe_allow_html=True)[cite: 6]
st.sidebar.markdown(f"<p style='margin:2px 0; font-size:0.85rem; color:#ede9fe;'>🏛️ {perfil.get('universidad', 'Pontificia Universidad Católica de Valparaíso')}</p>", unsafe_allow_html=True)[cite: 6]
st.sidebar.markdown(f"<p style='margin:2px 0 10px 0; font-size:0.85rem; color:#ede9fe;'>📍 {perfil.get('ubicacion', 'Valparaíso, Chile')}</p>", unsafe_allow_html=True)[cite: 6]

with st.sidebar.expander("⚙️ Editar Datos del Perfil"):[cite: 6]
    n_nom = st.text_input("Nombre:", value=perfil.get("nombre", "Francesca Fellay"))[cite: 6]
    n_uni = st.text_input("Universidad:", value=perfil.get("universidad", "Pontificia Universidad Católica de Valparaíso"))[cite: 6]
    n_ubi = st.text_input("Ubicación:", value=perfil.get("ubicacion", "Valparaíso, Chile"))[cite: 6]
    n_img = st.file_uploader("Foto de perfil (JPG/PNG):", type=["jpg", "jpeg", "png"])[cite: 6]
    
    if st.button("Guardar Perfil"):[cite: 6]
        db["perfil"]["nombre"] = n_nom[cite: 6]
        db["perfil"]["universidad"] = n_uni[cite: 6]
        db["perfil"]["ubicacion"] = n_ubi[cite: 6]
        if n_img is not None:
            r_av = os.path.join(DIR_PERFILES, "avatar_usuario.png")[cite: 6]
            with open(r_av, "wb") as f_av:
                f_av.write(n_img.getbuffer())[cite: 6]
            db["perfil"]["avatar"] = r_av[cite: 6]
        guardar_estado(db)[cite: 6]
        st.success("Perfil actualizado.")[cite: 6]
        st.rerun()[cite: 6]

st.sidebar.markdown("<hr style='border:0.5px solid rgba(255,255,255,0.2); margin:16px 0;'>", unsafe_allow_html=True)[cite: 6]

# --- SELECTOR DE MÓDULO ---
st.sidebar.markdown("### 📚 Selector de Módulo")[cite: 6]
lista_modulos = list(db["modulos"].keys())[cite: 6]
if not lista_modulos:
    db["modulos"]["6to Semestre TSL"] = {"carpetas": {}}[cite: 6]
    guardar_estado(db)[cite: 6]
    lista_modulos = ["6to Semestre TSL"][cite: 6]

modulo_actual = st.sidebar.selectbox("Módulo Activo:", lista_modulos)[cite: 6]

with st.sidebar.expander("➕ Crear Nuevo Módulo"):[cite: 6]
    nuevo_mod_nom = st.text_input("Nombre del nuevo módulo:")[cite: 6]
    if st.button("Crear Módulo"):[cite: 6]
        if nuevo_mod_nom.strip() and nuevo_mod_nom not in db["modulos"]:[cite: 6]
            db["modulos"][nuevo_mod_nom] = {"carpetas": {}}[cite: 6]
            guardar_estado(db)[cite: 6]
            st.success("Módulo creado con éxito.")[cite: 6]
            st.rerun()[cite: 6]

# --- HEADER BRAND ---
tz_cl = pytz.timezone("America/Santiago")[cite: 6]
hora_actual = datetime.now(tz_cl).strftime("%d/%m/%Y | %H:%M:%S")[cite: 6]

st.markdown(f"""
<div class='brand-navbar'>
    <div class='brand-title'>
        <span>⚡ SkillPath</span>
        <span style='font-size:0.9rem; font-weight:500; opacity:0.85;'>| Plataforma de Apuntes en Vivo & IA</span>
    </div>
    <div style='font-size:0.88rem; font-weight:600;'>🇨🇱 {hora_actual}</div>
</div>
""", unsafe_allow_html=True)[cite: 6]

pestañas_principales = st.tabs(["📁 Mis Carpetas & Clases", "🎙️ Grabaciones Originales"])[cite: 6]

# ==========================================
# 1. MIS CARPETAS & CLASES
# ==========================================
with pestañas_principales[0]:[cite: 6]
    carpetas_modulo = db["modulos"][modulo_actual]["carpetas"][cite: 6]
    total_carpetas = len(carpetas_modulo)[cite: 6]
    total_clases = sum(len(c.get("clases", [])) for c in carpetas_modulo.values())[cite: 6]
    
    st.markdown(f"""
    <div class='welcome-card'>
        <h2 style='margin:0 0 6px 0;'>¡Bienvenida de vuelta, {db['perfil']['nombre']}! 👋</h2>
        <p style='margin:0; opacity:0.9;'>Módulo actual: <b>{modulo_actual}</b>. Transcripción y viñetas automáticas en <b>Español Latino</b> con botones nativos.</p>
    </div>
    <div class='stats-grid'>
        <div class='stat-card-1'><div class='stat-value'>{total_carpetas}</div><div class='stat-label'>Materias / Carpetas</div></div>
        <div class='stat-card-2'><div class='stat-value'>{total_clases}</div><div class='stat-label'>Clases Procesadas</div></div>
        <div class='stat-card-3'><div class='stat-value'>{len(db['grabaciones'])}</div><div class='stat-label'>Audios Grabados</div></div>
        <div class='stat-card-4'><div class='stat-value'>⚡ En Vivo</div><div class='stat-label'>Botones Nativos</div></div>
    </div>
    """, unsafe_allow_html=True)[cite: 6]

    with st.expander("➕ Crear Nueva Carpeta de Materia en " + modulo_actual, expanded=(total_carpetas == 0)):[cite: 6]
        col_c1, col_c2 = st.columns([2, 1])[cite: 6]
        with col_c1:
            nom_carpeta = st.text_input("Nombre de la Materia / Ramo:", placeholder="Ej. Taller de Intervención Social")[cite: 6]
        with col_c2:
            desc_carpeta = st.text_input("Profesor / Descripción breve:")[cite: 6]
        
        if st.button("Crear Carpeta de Materia"):[cite: 6]
            if nom_carpeta.strip():[cite: 6]
                if nom_carpeta not in carpetas_modulo:[cite: 6]
                    carpetas_modulo[nom_carpeta] = {
                        "descripcion": desc_carpeta,
                        "fecha_creacion": datetime.now(tz_cl).strftime("%Y-%m-%d %H:%M"),
                        "clases": []
                    }[cite: 6]
                    guardar_estado(db)[cite: 6]
                    st.success(f"Carpeta '{nom_carpeta}' agregada al módulo.")[cite: 6]
                    st.rerun()[cite: 6]
                else:
                    st.error("Ya existe una carpeta con ese nombre en este módulo.")[cite: 6]

    st.markdown("---")[cite: 6]

    if not carpetas_modulo:[cite: 6]
        st.info(f"Aún no has creado carpetas en el módulo '{modulo_actual}'. Crea la primera materia arriba.")[cite: 6]
    else:
        lista_nombres_carpetas = list(carpetas_modulo.keys())[cite: 6]
        tabs_carpetas = st.tabs([f"📂 {nom}" for nom in lista_nombres_carpetas])[cite: 6]

        for idx_tab, tab_materia in enumerate(tabs_carpetas):[cite: 6]
            nombre_mat = lista_nombres_carpetas[idx_tab][cite: 6]
            info_mat = carpetas_modulo[nombre_mat][cite: 6]

            with tab_materia:
                st.markdown(f"### 📖 {nombre_mat}")[cite: 6]
                st.caption(f"Detalle: **{info_mat.get('descripcion', 'Sin descripción')}** | Creada: {info_mat.get('fecha_creacion')}")[cite: 6]
                
                nom_sesion_live = st.text_input("Tema / Título de la clase:", placeholder="Ej. Clase 1: Diagnóstico Comunitario", key=f"t_live_input_{nombre_mat}")[cite: 6]

                session_key_borrador = f"live_notes_draft_{modulo_actual}_{nombre_mat}"[cite: 6]
                session_key_last_proc = f"last_processed_audio_sig_{modulo_actual}_{nombre_mat}"[cite: 6]

                if session_key_borrador not in st.session_state:[cite: 6]
                    st.session_state[session_key_borrador] = ""[cite: 6]
                if session_key_last_proc not in st.session_state:[cite: 6]
                    st.session_state[session_key_last_proc] = ""[cite: 6]

                # --- CONTROL NATIVO OFICIAL DE STREAMLIT ---
                st.markdown("""
                <div class='app-card'>
                    <h4 style='margin:0 0 8px 0; color:#5b21b6;'>🎙️ Grabación en Vivo con Botones Nativos</h4>
                    <p style='color:#64748b; font-size:0.9rem; margin-bottom:12px;'>
                        Presiona el micrófono nativo para grabar. Cada vez que captures voz, la IA transcribirá y estructurará automáticamente los apuntes con viñetas y conceptos clave en español latino en el cuadro inferior.
                    </p>
                </div>
                """, unsafe_allow_html=True)[cite: 6]

                c_rec_live, c_up_live = st.columns([1.2, 1.2])[cite: 6]
                with c_rec_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>Grabar con Micrófono Nativo:</p>", unsafe_allow_html=True)[cite: 6]
                    audio_live_in = st.audio_input("Botones Oficiales (Grabar / Pausar / Detener):", key=f"live_audio_in_{modulo_actual}_{nombre_mat}")[cite: 6]

                with c_up_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>O Cargar Archivo de Audio:</p>", unsafe_allow_html=True)[cite: 6]
                    uploaded_live_in = st.file_uploader("Formatos (.wav, .mp3, .m4a):", type=["wav", "mp3", "m4a"], key=f"live_up_in_{modulo_actual}_{nombre_mat}")[cite: 6]

                audio_bytes_capturados = None[cite: 6]
                ext_capturado = "wav"[cite: 6]

                if audio_live_in is not None:[cite: 6]
                    audio_bytes_capturados = audio_live_in.getvalue()[cite: 6]
                    ext_capturado = "wav"[cite: 6]
                elif uploaded_live_in is not None:[cite: 6]
                    audio_bytes_capturados = uploaded_live_in.getvalue()[cite: 6]
                    ext_capturado = uploaded_live_in.name.split(".")[-1].lower()[cite: 6]

                # --- PIPELINE REACTIVO CONTINUO ---
                if audio_bytes_capturados is not None:[cite: 6]
                    audio_sig = f"{len(audio_bytes_capturados)}_{hash(audio_bytes_capturados[:64])}"[cite: 6]
                    if audio_sig != st.session_state[session_key_last_proc]:[cite: 6]
                        client = obtener_cliente_ia()[cite: 6]
                        if not client:[cite: 6]
                            st.error("⚠️ Clave GROQ_API_KEY no configurada en Secrets de Streamlit.")[cite: 6]
                        else:
                            with st.spinner("⚡ Transcribiendo con Whisper y estructurando apuntes en vivo..."):[cite: 6]
                                try:
                                    audio_buffer = io.BytesIO(audio_bytes_capturados)[cite: 6]
                                    audio_buffer.name = f"audio_temp.{ext_capturado}"[cite: 6]
                                    transcripcion = client.audio.transcriptions.create(
                                        model=MODELO_WHISPER,
                                        file=audio_buffer,
                                        language="es"
                                    )[cite: 6]
                                    texto_transcrito = transcripcion.text[cite: 6]

                                    apuntes_generados = estructurar_apuntes_groq(
                                        client=client,
                                        texto_transcrito=texto_transcrito,
                                        materia=nombre_mat,
                                        titulo=nom_sesion_live,
                                        borrador_previo=st.session_state[session_key_borrador]
                                    )[cite: 6]

                                    st.session_state[session_key_borrador] = apuntes_generados[cite: 6]
                                    st.session_state[session_key_last_proc] = audio_sig[cite: 6]

                                    # Guardado en grabaciones originales
                                    n_aud_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nombre_mat}.{ext_capturado}"[cite: 6]
                                    r_dest = os.path.join(DIR_AUDIO_RAW, n_aud_name)[cite: 6]
                                    with open(r_dest, "wb") as f_raw:[cite: 6]
                                        f_raw.write(audio_bytes_capturados)[cite: 6]
                                    
                                    db["grabaciones"].append({
                                        "titulo": nom_sesion_live if nom_sesion_live.strip() else f"Grabación {datetime.now(tz_cl).strftime('%d/%m/%Y %H:%M')}",
                                        "materia": nombre_mat,
                                        "modulo": modulo_actual,
                                        "fecha": datetime.now(tz_cl).strftime("%Y-%m-%d %H:%M"),
                                        "ruta": r_dest
                                    })[cite: 6]
                                    guardar_estado(db)[cite: 6]
                                    st.success("✅ ¡Apuntes redactados y estructurados con éxito!")[cite: 6]
                                except Exception as e:
                                    st.error(f"Error procesando con Groq: {e}")[cite: 6]

                # --- CUADRO EN VIVO: APUNTES ESTRUCTURADOS ---
                st.markdown("##### 📝 Cuadro de Apuntes Estructurados en Vivo (Español Latino):")[cite: 6]
                if st.session_state[session_key_borrador]:[cite: 6]
                    st.markdown(f"<div class='live-notes-box'>{st.session_state[session_key_borrador]}</div>", unsafe_allow_html=True)[cite: 6]

                    c_save1, c_save2 = st.columns([2, 1])[cite: 6]
                    with c_save1:
                        if st.button("💾 Guardar Clase en Cuaderno Permanente", key=f"btn_save_perm_{nombre_mat}"):[cite: 6]
                            titulo_final = nom_sesion_live.strip() if nom_sesion_live.strip() else f"Clase del {datetime.now(tz_cl).strftime('%d/%m/%Y %H:%M')}"[cite: 6]
                            info_mat["clases"].append({
                                "id": f"clase_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "titulo": titulo_final,
                                "fecha": datetime.now(tz_cl).strftime("%d/%m/%Y %H:%M"),
                                "contenido": st.session_state[session_key_borrador],
                                "chat": []
                            })[cite: 6]
                            guardar_estado(db)[cite: 6]
                            st.session_state[session_key_borrador] = ""[cite: 6]
                            st.session_state[session_key_last_proc] = ""[cite: 6]
                            st.success("¡Clase archivada exitosamente en tu cuaderno permanente!")[cite: 6]
                            st.rerun()[cite: 6]

                    with c_save2:
                        if st.button("🔄 Reiniciar Borrador en Vivo", key=f"btn_reset_live_{nombre_mat}"):[cite: 6]
                            st.session_state[session_key_borrador] = ""[cite: 6]
                            st.session_state[session_key_last_proc] = ""[cite: 6]
                            st.rerun()[cite: 6]
                else:
                    st.markdown("""
                    <div class='live-notes-box' style='color:#94a3b8; font-style:italic;'>
                        Presiona el botón nativo del micrófono arriba para empezar a grabar. La IA redactará aquí tus apuntes organizados en viñetas, conceptos clave y explicaciones en español latino sobre la marcha...
                    </div>
                    """, unsafe_allow_html=True)[cite: 6]

                st.markdown("---")[cite: 6]

                # --- HISTORIAL DE CLASES GUARDADAS EN LA MATERIA ---
                st.markdown("#### 📚 Cuaderno de Apuntes Guardados")[cite: 6]
                clases_guardadas = info_mat.get("clases", [])[cite: 6]
                
                if not clases_guardadas:[cite: 6]
                    st.info("Aún no has archivado clases en esta materia. Graba con el botón de arriba para comenzar.")[cite: 6]
                else:
                    for idx_c, clase in enumerate(reversed(clases_guardadas)):[cite: 6]
                        idx_real = len(clases_guardadas) - 1 - idx_c[cite: 6]
                        with st.expander(f"📝 {clase['titulo']} — ({clase['fecha']})", expanded=(idx_c == 0)):[cite: 6]
                            c_hist_content, c_hist_actions = st.columns([4, 1])[cite: 6]
                            with c_hist_content:
                                st.markdown(clase["contenido"])[cite: 6]
                            
                            with c_hist_actions:
                                st.download_button(
                                    "📥 Descargar (.txt)",
                                    data=clase["contenido"],
                                    file_name=f"{clase['titulo']}_Apuntes.txt",
                                    key=f"dl_txt_{clase['id']}"
                                )[cite: 6]
                                if st.button("🗑️ Eliminar Clase", key=f"del_cls_{clase['id']}"):[cite: 6]
                                    clases_guardadas.pop(idx_real)[cite: 6]
                                    guardar_estado(db)[cite: 6]
                                    st.success("Clase eliminada.")[cite: 6]
                                    st.rerun()[cite: 6]

                            st.markdown("---")[cite: 6]
                            
                            # Tutor Chat
                            st.markdown(f"##### 💬 Tutor IA: Consultas sobre '{clase['titulo']}'")[cite: 6]
                            historial_chat = clase.get("chat", [])[cite: 6]
                            for mensaje in historial_chat:[cite: 6]
                                if mensaje["rol"] == "user":[cite: 6]
                                    st.markdown(f"**Tú:** {mensaje['texto']}")[cite: 6]
                                else:
                                    st.markdown(f"**🤖 Tutor IA:** {mensaje['texto']}")[cite: 6]

                            with st.form(f"form_chat_{clase['id']}"):[cite: 6]
                                pregunta_usuario = st.text_input("Haz una pregunta sobre el contenido de esta clase:", placeholder="Ej. ¿Qué autores se citaron?", key=f"inp_chat_{clase['id']}")[cite: 6]
                                if st.form_submit_button("Consultar al Tutor") and pregunta_usuario.strip():[cite: 6]
                                    client = obtener_cliente_ia()[cite: 6]
                                    if client:[cite: 6]
                                        with st.spinner("Pensando respuesta..."):[cite: 6]
                                            try:
                                                resp_tutor = estructurar_apuntes_groq(
                                                    client=client,
                                                    texto_transcrito=f"Pregunta del alumno: {pregunta_usuario}",
                                                    materia=nombre_mat,
                                                    titulo=clase['titulo'],
                                                    borrador_previo=clase['contenido']
                                                )[cite: 6]
                                                if "chat" not in clases_guardadas[idx_real]:[cite: 6]
                                                    clases_guardadas[idx_real]["chat"] = [][cite: 6]
                                                
                                                clases_guardadas[idx_real]["chat"].append({"rol": "user", "texto": pregunta_usuario})[cite: 6]
                                                clases_guardadas[idx_real]["chat"].append({"rol": "ai", "texto": resp_tutor})[cite: 6]
                                                guardar_estado(db)[cite: 6]
                                                st.rerun()[cite: 6]
                                            except Exception as e:
                                                st.error(f"Error en tutor: {e}")[cite: 6]

# ==========================================
# 2. GRABACIONES ORIGINALES
# ==========================================
with pestañas_principales[1]:[cite: 6]
    st.markdown("""
    <div class='app-card'>
        <h3 style='margin:0 0 6px 0; color:#5b21b6;'>🎙️ Repositorio Central de Grabaciones Originales</h3>
        <p style='margin:0; color:#64748b;'>Todas las grabaciones de voz se almacenan de forma segura aquí para su reproducción o descarga.</p>
    </div>
    """, unsafe_allow_html=True)[cite: 6]

    grabaciones = db.get("grabaciones", [])[cite: 6]
    if not grabaciones:[cite: 6]
        st.info("No hay grabaciones de audio guardadas todavía.")[cite: 6]
    else:
        for idx_g, g in enumerate(reversed(grabaciones)):[cite: 6]
            idx_real_g = len(grabaciones) - 1 - idx_g[cite: 6]
            with st.container():[cite: 6]
                c_g1, c_g2 = st.columns([4, 1])[cite: 6]
                with c_g1:[cite: 6]
                    st.markdown(f"#### 🎵 {g['titulo']}")[cite: 6]
                    st.caption(f"Materia: **{g['materia']}** | Módulo: **{g.get('modulo', 'General')}** | Grabado: {g['fecha']}")[cite: 6]
                    if os.path.exists(g["ruta"]):[cite: 6]
                        with open(g["ruta"], "rb") as f_play:[cite: 6]
                            st.audio(f_play.read())[cite: 6]
                    else:
                        st.error("Archivo físico no encontrado.")[cite: 6]
                with c_g2:[cite: 6]
                    if os.path.exists(g["ruta"]):[cite: 6]
                        with open(g["ruta"], "rb") as f_dl:[cite: 6]
                            st.download_button(
                                "📥 Descargar Audio",
                                data=f_dl.read(),
                                file_name=os.path.basename(g["ruta"]),
                                key=f"dl_raw_{idx_real_g}"
                            )[cite: 6]
                    if st.button("🗑️ Eliminar Audio", key=f"del_raw_{idx_real_g}"):[cite: 6]
                        if os.path.exists(g["ruta"]):[cite: 6]
                            os.remove(g["ruta"])[cite: 6]
                        grabaciones.pop(idx_real_g)[cite: 6]
                        guardar_estado(db)[cite: 6]
                        st.success("Grabación eliminada.")[cite: 6]
                        st.rerun()[cite: 6]
                st.markdown("---")[cite: 6]

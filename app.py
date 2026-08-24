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
    except Exception as e:
        st.error(f"Error al conectar con Groq: {e}")
        return None

def ejecutar_chat_groq(client, prompt_sistema, prompt_usuario):
    # Detección dinámica del mejor modelo de texto disponible en tu cuenta
    modelos_preferidos = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    
    # Obtener modelos activos directamente desde la API
    try:
        lista_api = [m.id for m in client.models.list().data if "whisper" not in m.id]
    except Exception:
        lista_api = []

    candidatos = [m for m in modelos_preferidos if m in lista_api] + lista_api + modelos_preferidos

    for model_id in candidatos:
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": prompt_usuario}
                ],
                temperature=0.3
            )
            return resp.choices[0].message.content
        except Exception:
            continue
            
    raise Exception("No se encontró ningún modelo de texto compatible activo en Groq.")

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

/* DESPLEGABLES DEL ÁREA CENTRAL */
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

/* Inputs en Sidebar */
section[data-testid="stSidebar"] input[type="text"] {
    background-color: #ede9fe !important;
    color: #2e1065 !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Selector en Sidebar */
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

/* CONTENEDOR DE AUDIO NATIVO Y CARGADOR */
div[data-testid="stAudioInput"],
div[data-testid="stFileUploader"] {
    background-color: #ede9fe !important;
    border: 2px dashed #8b5cf6 !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
div[data-testid="stAudioInput"] *,
div[data-testid="stFileUploader"] * {
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
    max-height: 480px;
    overflow-y: auto;
    font-size: 0.96rem;
    color: #1e1b4b;
    line-height: 1.6;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.1);
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

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

st.sidebar.markdown(f"<h3 style='margin:0; font-size:1.15rem; color:#ffffff;'>{perfil.get('nombre', 'Francesca Fellay')}</h3>", unsafe_allow_html=True)
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
        <h2 style='margin:0 0 6px 0;'>¡Bienvenida de vuelta, {db['perfil']['nombre']}! 👋</h2>
        <p style='margin:0; opacity:0.9;'>Módulo actual: <b>{modulo_actual}</b>. Motor activo: <b>Groq Ultra-Speed</b>.</p>
    </div>
    <div class='stats-grid'>
        <div class='stat-card-1'><div class='stat-value'>{total_carpetas}</div><div class='stat-label'>Materias / Carpetas</div></div>
        <div class='stat-card-2'><div class='stat-value'>{total_clases}</div><div class='stat-label'>Clases Procesadas</div></div>
        <div class='stat-card-3'><div class='stat-value'>{len(db['grabaciones'])}</div><div class='stat-label'>Audios Grabados</div></div>
        <div class='stat-card-4'><div class='stat-value'>⚡ Groq IA</div><div class='stat-label'>Whisper + Llama</div></div>
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
                
                # --- SISTEMA DE GENERACIÓN DE APUNTES EN VIVO ---
                session_key_borrador = f"live_notes_draft_{modulo_actual}_{nombre_mat}"
                session_key_last_proc = f"last_processed_audio_sig_{modulo_actual}_{nombre_mat}"

                if session_key_borrador not in st.session_state:
                    st.session_state[session_key_borrador] = ""
                if session_key_last_proc not in st.session_state:
                    st.session_state[session_key_last_proc] = ""

                st.markdown("""
                <div class='app-card'>
                    <h4 style='margin:0 0 8px 0; color:#5b21b6;'>🎙️ Grabación en Vivo: Transcripción & Estructuración Instantánea</h4>
                    <p style='color:#64748b; font-size:0.9rem; margin-bottom:12px;'>
                        Graba con los botones nativos del micrófono. <b>Whisper Large</b> transcribirá la voz y <b>Groq</b> redactará y organizará la clase en viñetas, conceptos clave y explicaciones en tiempo real.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                nom_sesion_live = st.text_input("Tema / Título de la clase:", placeholder="Ej. Clase 1: Diagnóstico Comunitario", key=f"t_live_input_{nombre_mat}")

                # Entrada de voz nativa oficial de Streamlit
                c_rec_live, c_up_live = st.columns([1.2, 1.2])
                with c_rec_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>1. Grabar con Micrófono (Botones Nativos):</p>", unsafe_allow_html=True)
                    audio_live_in = st.audio_input("Presiona para Grabar / Pausar / Detener:", key=f"live_audio_in_{modulo_actual}_{nombre_mat}")

                with c_up_live:
                    st.markdown("<p style='color:#3b0764; font-weight:750; margin-bottom:6px;'>2. O Cargar Archivo de Audio:</p>", unsafe_allow_html=True)
                    uploaded_live_in = st.file_uploader("Formatos soportados (.wav, .mp3, .m4a):", type=["wav", "mp3", "m4a"], key=f"live_up_in_{modulo_actual}_{nombre_mat}")

                audio_bytes_capturados = None
                ext_capturado = "wav"

                if audio_live_in is not None:
                    audio_bytes_capturados = audio_live_in.getvalue()
                    ext_capturado = "wav"
                elif uploaded_live_in is not None:
                    audio_bytes_capturados = uploaded_live_in.getvalue()
                    ext_capturado = uploaded_live_in.name.split(".")[-1].lower()

                # PROCESAMIENTO REACTIVO EN TIEMPO REAL CON GROQ
                if audio_bytes_capturados is not None:
                    audio_sig = f"{len(audio_bytes_capturados)}_{hash(audio_bytes_capturados[:64])}"
                    
                    if audio_sig != st.session_state[session_key_last_proc]:
                        client = obtener_cliente_ia()
                        if not client:
                            st.error("⚠️ Clave GROQ_API_KEY no configurada en Secrets de Streamlit.")
                        else:
                            with st.spinner("⚡ Transcribiendo con Whisper y estructurando apuntes en vivo..."):
                                try:
                                    # 1. Transcripción con Whisper Large V3
                                    audio_buffer = io.BytesIO(audio_bytes_capturados)
                                    audio_buffer.name = f"audio_temp.{ext_capturado}"
                                    
                                    transcripcion = client.audio.transcriptions.create(
                                        model=MODELO_WHISPER,
                                        file=audio_buffer,
                                        language="es"
                                    )
                                    texto_transcrito = transcripcion.text

                                    # 2. Estructuración con Groq
                                    prompt_sys = f"Eres la asistente académica de excelencia de la estudiante universitaria Francesca Fellay en la materia '{nombre_mat}'."
                                    prompt_user = f"""
                                    Título de la clase: {nom_sesion_live if nom_sesion_live.strip() else 'Clase Universitaria'}.
                                    
                                    BORRADOR ACTUAL DE LOS APUNTES:
                                    \"\"\"
                                    {st.session_state[session_key_borrador] if st.session_state[session_key_borrador] else 'Comienzo de clase. Inicia la estructura formal.'}
                                    \"\"\"
                                    
                                    NUEVA TRANSCRIPCIÓN DE LA CLASE:
                                    \"\"\"
                                    {texto_transcrito}
                                    \"\"\"
                                    
                                    INSTRUCCIONES ESTRICTAS:
                                    1. Integra la nueva información al borrador sin repetir conceptos.
                                    2. Redacta apuntes claros y estructurados usando la siguiente plantilla:
                                       # 📌 Resumen Ejecutivo de la Clase
                                       ## 🎯 Objetivos y Temas Principales
                                       ## 📝 Desarrollo Detallado y Conceptos Clave (con viñetas claras, definiciones y explicaciones en negrita)
                                       ## 💡 Ejemplos Prácticos y Casos Mencionados
                                       ## ⚠️ Tareas, Acuerdos y Puntos Críticos para Estudiar
                                    """

                                    apuntes_generados = ejecutar_chat_groq(client, prompt_sys, prompt_user)
                                    
                                    st.session_state[session_key_borrador] = apuntes_generados
                                    st.session_state[session_key_last_proc] = audio_sig

                                    # Guardar archivo físico en el repositorio de grabaciones
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
                                    st.success("✅ ¡Apuntes redactados y organizados con éxito!")
                                except Exception as e:
                                    st.error(f"Error procesando con Groq: {e}")

                # --- CUADRO DE TEXTO: ORGANIZACIÓN DE APUNTES EN VIVO ---
                st.markdown("##### 📝 Cuadro de Apuntes Estructurados en Tiempo Real:")
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
                            st.success("¡Clase guardada exitosamente en tu cuaderno!")
                            st.rerun()

                    with c_save2:
                        if st.button("🔄 Reiniciar Borrador en Vivo", key=f"btn_reset_live_{nombre_mat}"):
                            st.session_state[session_key_borrador] = ""
                            st.session_state[session_key_last_proc] = ""
                            st.rerun()
                else:
                    st.markdown("""
                    <div class='live-notes-box' style='color:#94a3b8; font-style:italic;'>
                        Presiona el botón nativo del micrófono arriba para empezar a grabar. La IA irá redactando aquí los apuntes organizados en viñetas, conceptos clave y explicaciones a medida que se desarrolla la clase...
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
                                            p_sys = "Eres un tutor académico de apoyo para la estudiante Francesca Fellay."
                                            p_user = f"Contexto de los apuntes ({clase['titulo']}):\n{clase['contenido']}\n\nPregunta: {pregunta_usuario}"
                                            try:
                                                resp_tutor = ejecutar_chat_groq(client, p_sys, p_user)
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

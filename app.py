import os
import io
import json
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from PIL import Image
from google import genai
from google.genai import types

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="SkillPath — Cuadernos & Grabación en Vivo IA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RUTAS DE ALMACENAMIENTO PERSISTENTE ---
DIR_BASE = "cuadernos_data"
DIR_AUDIO_RAW = os.path.join(DIR_BASE, "grabaciones_originales")
DIR_PERFILES = os.path.join(DIR_BASE, "perfil_usuario")
FILE_DB = os.path.join(DIR_BASE, "cuadernos_db.json")

for d in [DIR_BASE, DIR_AUDIO_RAW, DIR_PERFILES]:
    os.makedirs(d, exist_ok=True)

MODELO_GEMINI = "gemini-3.6-flash"

# --- OBTENCION SEGURA DE API KEY ---
def obtener_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.environ.get("GEMINI_API_KEY", "")

API_KEY_GEMINI = obtener_api_key()

def obtener_cliente_ia():
    if not API_KEY_GEMINI:
        return None
    return genai.Client(api_key=API_KEY_GEMINI)

# --- ESTILOS CSS ---
st.markdown("""
<style>
html, body, [class*="css"], .stApp { 
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important; 
    background-color: #f4f5fa !important;
    color: #1e1b4b;
}

/* Header Brand */
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

/* BARRA LATERAL SKILLPATH */
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

/* Desplegables en Sidebar */
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
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[role="region"] {
    background-color: transparent !important;
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
div[data-testid="stExpander"] summary svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}
div[data-testid="stExpander"] div[role="region"] {
    background-color: #ffffff !important;
    color: #1e1b4b !important;
    padding: 18px !important;
}

/* Inputs en Sidebar */
section[data-testid="stSidebar"] input[type="text"], 
section[data-testid="stSidebar"] input[type="password"] {
    background-color: #ede9fe !important;
    color: #2e1065 !important;
    border: 1.5px solid #c4b5fd !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] input[type="text"]:focus {
    background-color: #ffffff !important;
    border-color: #fbbf24 !important;
    box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.3) !important;
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
section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
    fill: #2e1065 !important;
    color: #2e1065 !important;
}

/* Botones en Sidebar */
section[data-testid="stSidebar"] .stButton>button {
    background: #ede9fe !important;
    color: #4c1d95 !important;
    border: 1.5px solid #ddd6fe !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background: #ffffff !important;
    color: #311068 !important;
    border-color: #ffffff !important;
    transform: translateY(-1px);
}
section[data-testid="stSidebar"] .stButton>button p {
    color: #4c1d95 !important;
    font-weight: 800 !important;
}

/* Banner Dashboard y Tarjetas */
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
.stat-card-1 { background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); color: white; border-radius: 14px; padding: 18px; box-shadow: 0 4px 14px rgba(219, 39, 119, 0.25); }
.stat-card-2 { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); color: white; border-radius: 14px; padding: 18px; box-shadow: 0 4px 14px rgba(109, 40, 217, 0.25); }
.stat-card-3 { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border-radius: 14px; padding: 18px; box-shadow: 0 4px 14px rgba(29, 78, 216, 0.25); }
.stat-card-4 { background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: white; border-radius: 14px; padding: 18px; box-shadow: 0 4px 14px rgba(8, 145, 178, 0.25); }
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

/* Botones Principales */
.stButton>button {
    background: linear-gradient(135deg, #6214c7 0%, #7c24ec 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 9px 22px !important;
    font-weight: 750 !important;
    box-shadow: 0 4px 12px rgba(98, 20, 199, 0.25) !important;
    transition: all 0.2s ease !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #7c24ec 0%, #6214c7 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(98, 20, 199, 0.35) !important;
}
.stButton>button p {
    color: #ffffff !important;
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
div[data-testid="stDownloadButton"]>button:hover {
    background: #ddd6fe !important;
    color: #2e1065 !important;
}
div[data-testid="stDownloadButton"]>button p {
    color: #4c1d95 !important;
    font-weight: 750 !important;
}

input[type="text"], textarea {
    background-color: #f8fafc !important;
    color: #1e1b4b !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2) !important;
}

button[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #64748b !important;
    font-weight: 750 !important;
    padding: 10px 20px !important;
    border-radius: 8px 8px 0 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #6214c7 !important;
    border-bottom: 3.5px solid #6214c7 !important;
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

# --- BARRA LATERAL: PERFIL DE USUARIO ---
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

# --- HEADER BRAND SKILLPATH ---
tz_cl = pytz.timezone("America/Santiago")
hora_actual = datetime.now(tz_cl).strftime("%d/%m/%Y | %H:%M:%S")

st.markdown(f"""
<div class='brand-navbar'>
    <div class='brand-title'>
        <span>⚡ SkillPath</span>
        <span style='font-size:0.9rem; font-weight:500; opacity:0.85;'>| Plataforma de Apuntes Inteligentes & Audio en Vivo</span>
    </div>
    <div style='font-size:0.88rem; font-weight:600;'>🇨🇱 {hora_actual}</div>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS PRINCIPALES ---
pestañas_principales = st.tabs(["📁 Mis Carpetas & Clases", "🎙️ Grabaciones Originales"])

# ==========================================
# 1. MIS CARPETAS & CLASES (CUADERNOS)
# ==========================================
with pestañas_principales[0]:
    carpetas_modulo = db["modulos"][modulo_actual]["carpetas"]
    total_carpetas = len(carpetas_modulo)
    total_clases = sum(len(c.get("clases", [])) for c in carpetas_modulo.values())
    
    st.markdown(f"""
    <div class='welcome-card'>
        <h2 style='margin:0 0 6px 0;'>¡Bienvenida de vuelta, {db['perfil']['nombre']}! 👋</h2>
        <p style='margin:0; opacity:0.9;'>Módulo actual: <b>{modulo_actual}</b>. Transcripción y apuntes automáticos con Gemini 3.6 Flash.</p>
    </div>
    <div class='stats-grid'>
        <div class='stat-card-1'><div class='stat-value'>{total_carpetas}</div><div class='stat-label'>Materias / Carpetas</div></div>
        <div class='stat-card-2'><div class='stat-value'>{total_clases}</div><div class='stat-label'>Clases Procesadas</div></div>
        <div class='stat-card-3'><div class='stat-value'>{len(db['grabaciones'])}</div><div class='stat-label'>Audios Grabados</div></div>
        <div class='stat-card-4'><div class='stat-value'>IA Activa</div><div class='stat-label'>Gemini 3.6 Flash</div></div>
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
                
                st.markdown("""
                <div class='app-card'>
                    <h4 style='margin:0 0 10px 0; color:#5b21b6;'>🎙️ Grabación de Clase & Apuntes Automáticos con IA</h4>
                    <p style='color:#64748b; font-size:0.9rem; margin-bottom:14px;'>Haz clic en el micrófono para grabar la clase. Al terminar, Gemini 3.6 Flash generará tus apuntes estructurados y corregidos al instante.</p>
                </div>
                """, unsafe_allow_html=True)

                nom_sesion = st.text_input("Tema / Título de la sesión:", placeholder="Ej. Clase 1: Diagnóstico Comunitario", key=f"title_{nombre_mat}")

                col_rec, col_file = st.columns([1, 2])
                with col_rec:
                    st.markdown("**🎙️ Grabar con Micrófono:**")
                    audio_mic_bytes = audio_recorder(
                        text="Clic para Grabar",
                        recording_color="#e11d48",
                        neutral_color="#6214c7",
                        icon_size="2x",
                        key=f"audio_mic_{modulo_actual}_{nombre_mat}"
                    )
                with col_file:
                    st.markdown("**📁 O Subir Archivo de Audio:**")
                    archivo_subido = st.file_uploader("Formatos (.wav, .mp3, .m4a):", type=["wav", "mp3", "m4a"], key=f"up_{modulo_actual}_{nombre_mat}")

                # Audio final a procesar
                audio_bytes_final = None
                mime_final = "audio/wav"
                ext_final = "wav"

                if audio_mic_bytes is not None:
                    audio_bytes_final = audio_mic_bytes
                    mime_final = "audio/wav"
                    ext_final = "wav"
                    st.audio(audio_bytes_final, format="audio/wav")
                elif archivo_subido is not None:
                    audio_bytes_final = archivo_subido.read()
                    ext_final = archivo_subido.name.split(".")[-1].lower()
                    mime_map = {"wav": "audio/wav", "mp3": "audio/mp3", "m4a": "audio/mp4"}
                    mime_final = mime_map.get(ext_final, "audio/wav")
                    st.audio(audio_bytes_final, format=mime_final)

                if audio_bytes_final is not None:
                    if st.button("✨ Procesar Audio y Generar Apuntes Estructurados", key=f"btn_gen_{nombre_mat}"):
                        client = obtener_cliente_ia()
                        if not client:
                            st.error("⚠️ Clave GEMINI_API_KEY no configurada en los Secrets de Streamlit.")
                        else:
                            titulo_final = nom_sesion.strip() if nom_sesion.strip() else f"Clase del {datetime.now(tz_cl).strftime('%d/%m/%Y %H:%M')}"
                            
                            # Guardar archivo físico en grabaciones
                            nombre_archivo_audio = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nombre_mat}.{ext_final}"
                            ruta_audio_dest = os.path.join(DIR_AUDIO_RAW, nombre_archivo_audio)
                            with open(ruta_audio_dest, "wb") as f_aud:
                                f_aud.write(audio_bytes_final)
                            
                            db["grabaciones"].append({
                                "titulo": titulo_final,
                                "materia": nombre_mat,
                                "modulo": modulo_actual,
                                "fecha": datetime.now(tz_cl).strftime("%Y-%m-%d %H:%M"),
                                "ruta": ruta_audio_dest
                            })

                            with st.spinner("🤖 Gemini 3.6 Flash está escuchando el audio, corrigiendo y redactando los apuntes estructurados..."):
                                prompt_apuntes = f"""
                                Eres una asistente universitaria de excelencia para la estudiante Francesca Fellay.
                                Escucha con total precisión este audio de la clase universitaria de '{nombre_mat}'.
                                Título de la sesión: {titulo_final}.
                                
                                Genera unos apuntes completos, organizados y profesionales con:
                                # 📌 Resumen Ejecutivo de la Clase
                                ## 🎯 Objetivos y Temas Principales Abordados
                                ## 📝 Desarrollo Detallado y Conceptos Clave (viñetas, definiciones y explicaciones claras)
                                ## 💡 Ejemplos Prácticos y Casos Mencionados
                                ## ⚠️ Tareas, Acuerdos y Puntos Críticos para Estudiar
                                """
                                try:
                                    resp = client.models.generate_content(
                                        model=MODELO_GEMINI,
                                        contents=[
                                            types.Part.from_bytes(data=audio_bytes_final, mime_type=mime_final),
                                            prompt_apuntes
                                        ]
                                    )
                                    info_mat["clases"].append({
                                        "id": f"clase_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                        "titulo": titulo_final,
                                        "fecha": datetime.now(tz_cl).strftime("%d/%m/%Y %H:%M"),
                                        "contenido": resp.text,
                                        "chat": []
                                    })
                                    guardar_estado(db)
                                    st.success("¡Apuntes generados y guardados exitosamente!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al procesar el audio con Gemini: {e}")

                st.markdown("---")

                # Cuaderno de apuntes
                st.markdown("#### 📚 Cuaderno de Apuntes Registrados")
                clases_guardadas = info_mat.get("clases", [])
                
                if not clases_guardadas:
                    st.info("Aún no hay apuntes en esta materia. Graba con tu micrófono arriba para comenzar.")
                else:
                    for idx_c, clase in enumerate(reversed(clases_guardadas)):
                        idx_real = len(clases_guardadas) - 1 - idx_c
                        with st.expander(f"📝 {clase['titulo']} — ({clase['fecha']})", expanded=(idx_c == 0)):
                            col_ed1, col_ed2 = st.columns([4, 1])
                            with col_ed1:
                                st.markdown("##### ✏️ Editor de Apuntes en Vivo:")
                                nuevo_texto = st.text_area(
                                    "Puedes editar tus apuntes en tiempo real:",
                                    value=clase["contenido"],
                                    height=350,
                                    key=f"edit_area_{clase['id']}"
                                )
                                if st.button("💾 Guardar Cambios en los Apuntes", key=f"btn_save_{clase['id']}"):
                                    clases_guardadas[idx_real]["contenido"] = nuevo_texto
                                    guardar_estado(db)
                                    st.success("Apuntes actualizados.")
                                    st.rerun()
                            
                            with col_ed2:
                                st.markdown("##### ⚙️ Acciones:")
                                st.download_button(
                                    "📥 Descargar Apuntes (.txt)",
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
                            st.markdown(f"##### 💬 Tutor IA: Preguntas y Dudas sobre '{clase['titulo']}'")
                            historial_chat = clase.get("chat", [])
                            for mensaje in historial_chat:
                                if mensaje["rol"] == "user":
                                    st.markdown(f"**Tú:** {mensaje['texto']}")
                                else:
                                    st.markdown(f"**🤖 Gemini:** {mensaje['texto']}")

                            with st.form(f"form_chat_{clase['id']}"):
                                pregunta_usuario = st.text_input("Hazle una pregunta a la IA sobre esta clase:", placeholder="Ej. Explícame el concepto principal con otro ejemplo...")
                                submit_chat = st.form_submit_button("Enviar Pregunta")
                                
                                if submit_chat and pregunta_usuario.strip():
                                    client = obtener_cliente_ia()
                                    if not client:
                                        st.error("API Key de Gemini no configurada.")
                                    else:
                                        with st.spinner("Pensando respuesta..."):
                                            prompt_chat = f"""
                                            Eres un tutor académico de apoyo para la estudiante Francesca Fellay.
                                            Contexto de los apuntes de la clase ({clase['titulo']}):
                                            {clase['contenido']}
                                            
                                            Pregunta de la estudiante:
                                            {pregunta_usuario}
                                            
                                            Responde de forma pedagógica, clara y directa.
                                            """
                                            try:
                                                resp_chat = client.models.generate_content(
                                                    model=MODELO_GEMINI,
                                                    contents=prompt_chat
                                                )
                                                if "chat" not in clases_guardadas[idx_real]:
                                                    clases_guardadas[idx_real]["chat"] = []
                                                
                                                clases_guardadas[idx_real]["chat"].append({"rol": "user", "texto": pregunta_usuario})
                                                clases_guardadas[idx_real]["chat"].append({"rol": "ai", "texto": resp_chat.text})
                                                guardar_estado(db)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error en el chat: {e}")

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
                        st.error("Archivo de audio no encontrado en el almacenamiento local.")
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

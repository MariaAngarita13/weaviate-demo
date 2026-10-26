"""Interfaz web (Streamlit) para demostrar búsqueda vectorial con Weaviate."""
import streamlit as st
import weaviate
from weaviate.classes.query import Filter, MetadataQuery
from sentence_transformers import SentenceTransformer

from config import COLLECTION, MODEL_NAME

st.set_page_config(page_title="Demo Weaviate", page_icon="🔎", layout="wide")


@st.cache_resource
def get_model():
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource
def get_client():
    return weaviate.connect_to_local()


model = get_model()
try:
    client = get_client()
    if not client.collections.exists(COLLECTION):
        st.error("La colección no existe. Ejecuta primero: `python ingest.py`")
        st.stop()
    coleccion = client.collections.get(COLLECTION)
except Exception as e:
    st.error(f"No se pudo conectar a Weaviate. ¿Corre `docker compose up -d`?\n\n{e}")
    st.stop()

st.title("🔎 Búsqueda semántica con Weaviate")
st.caption("Busca por significado, no por palabras exactas. Prueba: *'cómo cuidar mi corazón'*, "
           "*'aprender sobre IA'*, *'destinos de playa'*.")

# ---- Barra lateral ----
with st.sidebar:
    st.header("Opciones")
    modo = st.radio("Tipo de búsqueda",
                    ["Semántica (vectorial)", "Híbrida (vector + palabras clave)", "Solo palabras clave (BM25)"])
    categorias = ["Todas", "Tecnología", "Salud", "Deportes", "Cocina", "Viajes"]
    categoria = st.selectbox("Filtrar por categoría", categorias)
    limite = st.slider("Resultados", 1, 10, 5)
    alpha = 0.5
    if modo.startswith("Híbrida"):
        alpha = st.slider("Alpha (0 = palabras, 1 = vector)", 0.0, 1.0, 0.5, 0.1)
    total = coleccion.aggregate.over_all(total_count=True).total_count
    st.metric("Documentos en Weaviate", total)

tab_buscar, tab_agregar, tab_datos = st.tabs(["Buscar", "Agregar documento", "Ver datos"])

# ---- Pestaña Buscar ----
with tab_buscar:
    consulta = st.text_input("Escribe tu búsqueda", placeholder="Ej: consejos para descansar mejor")
    if consulta:
        filtro = None if categoria == "Todas" else Filter.by_property("categoria").equal(categoria)
        vector = model.encode(consulta).tolist()

        if modo.startswith("Semántica"):
            res = coleccion.query.near_vector(
                near_vector=vector, limit=limite, filters=filtro,
                return_metadata=MetadataQuery(distance=True))
        elif modo.startswith("Híbrida"):
            res = coleccion.query.hybrid(
                query=consulta, vector=vector, alpha=alpha, limit=limite, filters=filtro,
                return_metadata=MetadataQuery(score=True))
        else:
            res = coleccion.query.bm25(
                query=consulta, limit=limite, filters=filtro,
                return_metadata=MetadataQuery(score=True))

        if not res.objects:
            st.warning("Sin resultados (la búsqueda por palabras exige coincidencias exactas).")
        for obj in res.objects:
            p, m = obj.properties, obj.metadata
            if m.distance is not None:
                similitud = f"Similitud: **{(1 - m.distance) * 100:.1f}%**"
            else:
                similitud = f"Score: **{m.score:.3f}**"
            with st.container(border=True):
                st.subheader(p["titulo"])
                st.write(p["contenido"])
                st.caption(f"🏷️ {p['categoria']}  |  {similitud}")

# ---- Pestaña Agregar ----
with tab_agregar:
    with st.form("nuevo"):
        t = st.text_input("Título")
        c = st.text_area("Contenido")
        cat = st.selectbox("Categoría", categorias[1:])
        enviar = st.form_submit_button("Guardar en Weaviate")
    if enviar:
        if t and c:
            vec = model.encode(f"{t}. {c}").tolist()
            coleccion.data.insert(
                properties={"titulo": t, "contenido": c, "categoria": cat}, vector=vec)
            st.success("Documento guardado. Ya puedes encontrarlo en la pestaña Buscar.")
        else:
            st.error("Completa título y contenido.")

# ---- Pestaña Datos ----
with tab_datos:
    for obj in coleccion.query.fetch_objects(limit=100).objects:
        p = obj.properties
        st.markdown(f"**{p['titulo']}** · _{p['categoria']}_  \n{p['contenido']}")

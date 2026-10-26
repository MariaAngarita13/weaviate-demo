# Demo de búsqueda vectorial con Weaviate

## Requisitos
- Docker Desktop (o Docker + Compose)
- Python 3.9 - 3.12

## Pasos
```bash
# 1. Levantar Weaviate (la base de datos)
docker compose up -d

# 2. Entorno virtual e instalación
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Crear la colección y cargar datos
python ingest.py

# 4. Lanzar la app
streamlit run app.py
```
Abre http://localhost:8501

## Comandos útiles
- Ver estado: `curl http://localhost:8080/v1/.well-known/ready`
- Detener: `docker compose down`
- Borrar todo (incluye datos): `docker compose down -v`

"""Crea la colección en Weaviate y carga los datos con sus vectores."""
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from sentence_transformers import SentenceTransformer

from config import COLLECTION, MODEL_NAME
from data import ARTICULOS


def main():
    print("Conectando a Weaviate (localhost:8080)...")
    client = weaviate.connect_to_local()
    try:
        # 1) Recrear la colección desde cero (el "esquema" de la base de datos)
        if client.collections.exists(COLLECTION):
            client.collections.delete(COLLECTION)
            print(f"Colección '{COLLECTION}' anterior eliminada.")

        client.collections.create(
            name=COLLECTION,
            vectorizer_config=Configure.Vectorizer.none(),  # vectores propios
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=VectorDistances.COSINE
            ),
            properties=[
                Property(name="titulo", data_type=DataType.TEXT),
                Property(name="contenido", data_type=DataType.TEXT),
                Property(name="categoria", data_type=DataType.TEXT),
            ],
        )
        print(f"Colección '{COLLECTION}' creada.")

        # 2) Generar embeddings (título + contenido)
        print(f"Cargando modelo {MODEL_NAME} (primera vez descarga ~470 MB)...")
        model = SentenceTransformer(MODEL_NAME)
        textos = [f"{a['titulo']}. {a['contenido']}" for a in ARTICULOS]
        vectores = model.encode(textos, show_progress_bar=True)

        # 3) Insertar en lote objeto + vector
        coleccion = client.collections.get(COLLECTION)
        with coleccion.batch.dynamic() as batch:
            for articulo, vector in zip(ARTICULOS, vectores):
                batch.add_object(properties=articulo, vector=vector.tolist())

        if coleccion.batch.failed_objects:
            print("Fallaron objetos:", coleccion.batch.failed_objects[:3])
        total = coleccion.aggregate.over_all(total_count=True).total_count
        print(f"Listo: {total} artículos almacenados en Weaviate.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

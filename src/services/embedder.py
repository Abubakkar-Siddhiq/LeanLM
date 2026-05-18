from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

class Embedder:

    def embed(self, text: str):
        return model.encode(text).tolist()
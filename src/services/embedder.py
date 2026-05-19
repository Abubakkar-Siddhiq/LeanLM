from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self):
        self._model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def embed(self, text: str):
        return self._model.encode(text).tolist()
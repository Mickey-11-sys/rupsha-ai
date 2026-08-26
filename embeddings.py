from sentence_transformers import SentenceTransformer
import config
import time

_model = None

def load_model():
    global _model
    if _model is None:
        print("RUPSHA: Loading embedding model...", flush=True)
        t0 = time.time()
        try:
            _model = SentenceTransformer(config.EMBEDDING_MODEL, device='cpu')
            print(f"RUPSHA: Model loaded in {time.time()-t0:.1f}s", flush=True)
        except Exception as e:
            print(f"RUPSHA: Model load FAILED: {e}", flush=True)
            raise
    return _model

def get_embedding(text):
    if not text or not isinstance(text, str):
        text = ""
    model = load_model()
    emb = model.encode(text, convert_to_numpy=True)
    return emb.tolist()

def get_embeddings(text_list):
    if not text_list:
        return []
    model = load_model()
    embs = model.encode(text_list, convert_to_numpy=True)
    return embs.tolist()

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDING_DIR = DATA_DIR / "embeddings"

for _d in (RAW_DIR, PROCESSED_DIR, EMBEDDING_DIR):
    _d.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "gemini-embedding-001"
RANDOM_SEED = 42

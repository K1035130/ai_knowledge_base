from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDING_DIR = DATA_DIR / "embeddings"

for _d in (RAW_DIR, PROCESSED_DIR, EMBEDDING_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# SiliconFlow speaks the OpenAI-compatible protocol; override SILICONFLOW_BASE_URL in .env to
# point the same client at any other OpenAI-compatible provider.
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024  # bge-m3 returns a fixed 1024-d vector — no output_dimensionality knob to shrink it
CHAT_MODEL = "Qwen/Qwen3-8B"
RANDOM_SEED = 42

"""Configuration for the helmet crawler agent."""

import os

# --- Ollama / LLM ---
# Inference runs in the Ollama server. For CUDA/GPU, enable a GPU session (e.g. Kaggle
# accelerator) before `ollama serve`, then verify with `nvidia-smi` / `ollama ps`.
# Optional: CUDA_VISIBLE_DEVICES=0 for the ollama serve process.
OLLAMA_MODEL = "llava:7b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# --- YouTube Search ---
SEARCH_QUERIES = [
    "Vietnam traffic no helmet motorcycle",
    "giao thong Viet Nam khong doi mu bao hiem",
    "camera giao thong Viet Nam",
    "khong doi mu bao hiem",
    "Vietnam motorbike no helmet dashcam",
    "vi pham giao thong khong mu bao hiem",
]
MAX_VIDEOS_PER_QUERY = 3
MAX_VIDEOS_TOTAL = 10
MAX_VIDEO_DURATION = 300  # seconds

# --- Download ---
VIDEO_RESOLUTION = "480p"
DOWNLOAD_DIR = "downloads"

# --- Frame Extraction ---
FRAME_INTERVAL = 2  # seconds between extracted frames
DUPLICATE_THRESHOLD = 10  # dhash hamming distance; lower = stricter dedup

# --- Detection ---
TWO_STAGE_DETECTION = True
CONFIDENCE_FILTER = ["high", "medium"]
RETRY_ON_PARSE_FAIL = True

STAGE1_PROMPT = (
    "Does this image show any person on a motorcycle or street "
    "who is NOT wearing a helmet? Answer only YES or NO."
)

STAGE2_PROMPT = (
    "You are a traffic safety analyst inspecting a Vietnamese street scene. "
    "List every person NOT wearing a helmet. For each person, provide: "
    "position in image (left/center/right), activity (riding/passenger/pedestrian), "
    "and confidence (high/medium/low). Reply ONLY with valid JSON:\n"
    '{"violations": [{"position": "...", "activity": "...", "confidence": "..."}], "count": N}'
)

STAGE2_RETRY_PROMPT = (
    "Look at this Vietnamese traffic image again. "
    "How many people are NOT wearing helmets? "
    'Reply with JSON: {"violations": [{"position": "left/center/right", '
    '"activity": "riding/passenger/pedestrian", "confidence": "high/medium/low"}], '
    '"count": N}'
)

# --- Output ---
OUTPUT_DIR = "output/no_helmet"
RESULTS_CSV = "output/results.csv"

# Kaggle-aware paths
if os.path.exists("/kaggle/working"):
    _BASE = "/kaggle/working"
    DOWNLOAD_DIR = os.path.join(_BASE, DOWNLOAD_DIR)
    OUTPUT_DIR = os.path.join(_BASE, OUTPUT_DIR)
    RESULTS_CSV = os.path.join(_BASE, RESULTS_CSV)

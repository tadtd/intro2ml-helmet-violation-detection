"""Print resolved crawler settings (useful on Kaggle after config path overrides)."""

from __future__ import annotations

import config


def main() -> None:
    print("Ollama host     :", config.OLLAMA_HOST)
    print("Model           :", config.OLLAMA_MODEL)
    print("Search queries  :", len(config.SEARCH_QUERIES))
    print("Max videos      :", config.MAX_VIDEOS_TOTAL)
    print("Frame interval  :", config.FRAME_INTERVAL, "s")
    print("Output dir      :", config.OUTPUT_DIR)
    print("Results CSV     :", config.RESULTS_CSV)


if __name__ == "__main__":
    main()

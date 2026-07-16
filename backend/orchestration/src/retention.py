import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestration.retention")


def run_retention_check():
    logger.info("Video retention pruning is disabled; uploaded videos are kept for review and course demos")


if __name__ == "__main__":
    # Standard retention loop running every hour
    while True:
        run_retention_check()
        time.sleep(3600)  # Sleep for 1 hour

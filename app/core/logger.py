# app/core/logger.py

# This is for logging any errors or warnings or info in the terminal we can also use this in production like we can see all the logs.
# so after this setup just call logger.info('gsdjasgdagd')/logger.warning('sdgsdgjdgjsd') anything like that the result will be printed in the terminal
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
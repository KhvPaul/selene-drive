import logging

from config import settings

FORMAT = "[%(asctime)s  %(name)s: %(filename)s: line %(lineno)s -> (%(levelname)s)]  %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S", level=settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

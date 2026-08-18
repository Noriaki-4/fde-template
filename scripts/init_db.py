#!/usr/bin/env python3
"""Database 初期化スクリプト"""

import sys
from backend.database.db import init_db, drop_db
import structlog

logger = structlog.get_logger()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        logger.info("Dropping database...")
        drop_db()
        logger.info("Database dropped")
    else:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized")

if __name__ == "__main__":
    main()

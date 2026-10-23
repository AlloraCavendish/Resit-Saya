# Purpose: Scheduled background task to purge expired soft-deleted receipts.
# Security: Automatically enforces data retention policy by calling purge service with fresh DB session.

import logging

from app.db import SessionLocal
from app.services.purge import purge_expired_deleted_receipts

logger = logging.getLogger("resitsaya.jobs")


def run_scheduled_purge() -> None:
    """Execute scheduled purge of expired receipts using an isolated database session."""
    logger.info("Starting scheduled retention purge job...")
    db = SessionLocal()
    try:
        purged = purge_expired_deleted_receipts(db)
        logger.info(f"Scheduled retention purge completed. Purged {purged} receipts.")
    except Exception as e:
        logger.error(f"Error during scheduled retention purge: {e}", exc_info=True)
    finally:
        db.close()

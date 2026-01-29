import argparse
import logging
import os
from typing import Set

from app.core.settings import settings
from app.db.database import SessionLocal
from app.db.models import FileSystem
from app.services.storage import storage_client

logger = logging.getLogger(__name__)


def cleanup_cache(dry_run: bool) -> bool:
    cache_path = settings.kg_cache_path
    if not os.path.exists(cache_path):
        logger.info("Cache file not found: %s", cache_path)
        return False
    if dry_run:
        logger.info("Dry run: would remove cache file %s", cache_path)
        return True
    os.remove(cache_path)
    logger.info("Removed cache file %s", cache_path)
    return True


def _load_referenced_keys() -> Set[str]:
    db = SessionLocal()
    try:
        rows = (
            db.query(FileSystem.storage_key)
            .filter(FileSystem.storage_key.isnot(None))
            .all()
        )
        return {row[0] for row in rows if row[0]}
    finally:
        db.close()


def cleanup_orphaned_objects(dry_run: bool, limit: int | None = None) -> int:
    if not storage_client.enabled or not storage_client.client:
        logger.info("Object storage disabled; skipping orphan cleanup.")
        return 0

    referenced_keys = _load_referenced_keys()
    prefix = settings.s3_prefix
    paginator = storage_client.client.get_paginator("list_objects_v2")

    deleted = 0
    for page in paginator.paginate(Bucket=storage_client.bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key")
            if not key or key in referenced_keys:
                continue
            if dry_run:
                logger.info("Dry run: would delete object %s", key)
            else:
                storage_client.client.delete_object(Bucket=storage_client.bucket, Key=key)
                logger.info("Deleted object %s", key)
            deleted += 1
            if limit and deleted >= limit:
                logger.info("Reached delete limit %s", limit)
                return deleted

    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description="Neptune cleanup utilities")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    parser.add_argument("--prune-cache", action="store_true", help="Remove knowledge graph cache file")
    parser.add_argument(
        "--prune-orphans",
        action="store_true",
        help="Remove orphaned objects from S3-compatible storage",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of deletions")

    args = parser.parse_args()

    if args.prune_cache:
        cleanup_cache(args.dry_run)
    if args.prune_orphans:
        cleanup_orphaned_objects(args.dry_run, args.limit)

    if not args.prune_cache and not args.prune_orphans:
        logger.info("No cleanup actions requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

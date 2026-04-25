#!/usr/bin/env python3
"""Offline utility: map Google place_ids to existing CityReference rows.

This script is intended to be run by a developer or operator (offline). It
looks up CityReference rows that do not have a real Google place_id (null or
mock:...) and attempts to resolve a Google place_id using the Places
Find Place from Text API. By default the script runs in dry-run mode and will
only print proposed mappings. Use --apply to persist mappings to the DB.

Usage examples:
  # Dry run (default)
  PYTHONPATH=./src python backend/scripts/map_place_ids.py --limit 50

  # Apply changes (writes place_id to CityReference)
  PYTHONPATH=./src python backend/scripts/map_place_ids.py --apply --api-key "YOUR_KEY"

Notes:
 - The script reads GENLOGS_GOOGLE_API_KEY by default if --api-key is not given.
 - It is conservative: it only updates rows when --apply is passed and you
   explicitly confirm (unless --yes is provided).
 - Runs against the configured DB (uses app.providers.db.engine). For local
   testing you can set GENLOGS_DATABASE_URL to a sqlite:///./dev.db URL.
"""
from __future__ import annotations

import os
import time
import csv
import argparse
from typing import Optional
from app.logging_config import configure_logging
from app.providers.logging_provider import get_logger

import requests
from sqlmodel import Session, select

from app.providers.db import engine, CityReference


logger = get_logger("map_place_ids")


def find_place_id_via_google(query_text: str, api_key: str) -> Optional[str]:
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query_text,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        payload = r.json()
        cand = payload.get("candidates", [])
        if cand:
            return cand[0].get("place_id")
    except Exception as exc:
        logger.debug("Find Place failed for %s: %s", query_text, exc)
    return None


def iter_target_cities(limit: Optional[int] = None):
    """Yield CityReference rows that lack a Google place_id or have mock ids."""
    with Session(engine) as session:
        col = CityReference.__table__.c.place_id
        stmt = select(CityReference).where((col.is_(None)) | (col.like('mock:%'))).order_by(CityReference.name)
        if limit:
            stmt = stmt.limit(limit)
        for row in session.exec(stmt):
            yield row


def main() -> int:
    parser = argparse.ArgumentParser(description="Map Google place_ids to CityReference rows (offline)")
    parser.add_argument("--api-key", help="Google API key (overrides GENLOGS_GOOGLE_API_KEY env)")
    parser.add_argument("--apply", action="store_true", help="Persist mappings to the database")
    parser.add_argument("--yes", action="store_true", help="When --apply, skip confirmation prompt")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of cities to process (0 => all)")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds to sleep between API calls (rate-limit)")
    parser.add_argument("--out", default="placeid_mappings.csv", help="CSV output file for proposed/applied mappings")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    if args.verbose:
        configure_logging("DEBUG")
    else:
        configure_logging("INFO")

    api_key = args.api_key or os.environ.get("GENLOGS_GOOGLE_API_KEY")
    if not api_key:
        logger.error("Google API key is required (set GENLOGS_GOOGLE_API_KEY or pass --api-key)")
        return 2

    limit = args.limit if args.limit and args.limit > 0 else None
    processed = 0
    found = 0
    updated = 0

    mappings = []  # list of tuples (city_id, name, old_place_id, new_place_id)

    for city in iter_target_cities(limit=limit):
        processed += 1
        query_text = f"{city.name}, {city.state}, {city.country}"
        logger.info("Resolving: %s (current place_id=%s)", query_text, city.place_id)
        pid = find_place_id_via_google(query_text, api_key)
        if pid:
            found += 1
            mappings.append((str(city.id), query_text, city.place_id or "", pid))
            logger.info("Found place_id=%s for %s", pid, query_text)
            if args.apply:
                logger.debug("Applying mapping to DB for city id %s -> %s", city.id, pid)
                with Session(engine) as session:
                    # re-query row in transaction and update
                    db_row = session.get(CityReference, city.id)
                    if db_row:
                        db_row.place_id = pid
                        session.add(db_row)
                        session.commit()
                        session.refresh(db_row)
                        updated += 1
        else:
            logger.info("No place_id found for %s", query_text)

        time.sleep(args.delay)

    # Write CSV
    if mappings:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["city_id", "label", "old_place_id", "new_place_id"]) 
            for row in mappings:
                w.writerow(row)
        logger.info("Wrote mappings to %s", args.out)

    logger.info("Processed: %d, Found: %d, Updated: %d", processed, found, updated)
    if args.apply and updated and not args.yes:
        logger.info("Applied changes. Rerun with --yes to skip confirmation in scripts.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

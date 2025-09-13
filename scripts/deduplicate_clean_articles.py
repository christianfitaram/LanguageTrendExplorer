#!/usr/bin/env python3
"""
dedupe_clean_articles.py

Deduplicate documents in the `clean_articles` collection.

Default strategy:
- Duplicate key: (sample, url)
- Keep: oldest (_id ascending)
- Dry-run by default (no deletions)
- Optionally enforce a unique index on (sample, url)

Env:
  MONGODB_URI (e.g. mongodb://localhost:27017)
  MONGO_DB_NAME (e.g. trending_words)

Usage examples:
  # Preview duplicates per sample (no deletes)
  python dedupe_clean_articles.py --scope per-sample --dry-run

  # Actually delete, keep newest, per specific sample
  python dedupe_clean_articles.py --scope per-sample --sample-id 2-2025-08-10 --keep newest

  # Global dedupe by URL only (rarely recommended), keep oldest
  python dedupe_clean_articles.py --scope global --key url --keep oldest

  # After cleaning, add a unique index to prevent future duplicates
  python dedupe_clean_articles.py --ensure-unique-index
"""
from __future__ import annotations
import os
import argparse
from typing import List, Dict, Any, Tuple
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv


def get_db():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    dbname = os.getenv("MONGODB_DB")
    client = MongoClient(uri)
    return client[dbname]


def build_group_key(doc: Dict[str, Any], key: str, scope: str) -> Tuple:
    """
    key: 'sample_url' | 'url'
    scope: 'per-sample' | 'global'
    """
    url = (doc.get("url") or "").strip()
    sample = (doc.get("sample") or "").strip()

    if key == "url":
        # Deduplicate only by URL (across all samples if scope=global; otherwise it's equivalent)
        return (url,)

    # default: sample_url (tuple)
    if scope == "per-sample":
        return (sample, url)
    # 'global' + sample_url key still considers sample+url; use --key url for truly global URL-only
    return (sample, url)


def find_duplicates(coll, scope: str, key: str, sample_id: str | None) -> List[List[Dict[str, Any]]]:
    """
    Returns a list of duplicate groups. Each group is a list of docs sharing the dedupe key.
    """
    query = {}
    if scope == "per-sample" and sample_id:
        query = {"sample": sample_id}

    # Only fetch needed fields to lower memory
    cursor = coll.find(query, {"_id": 1, "url": 1, "sample": 1, "scraped_at": 1})
    groups = {}
    for doc in cursor:
        gk = build_group_key(doc, key=key, scope=scope)
        groups.setdefault(gk, []).append(doc)

    dup_groups = [docs for docs in groups.values() if len(docs) > 1]
    return dup_groups


def choose_to_keep(docs: List[Dict[str, Any]], keep: str) -> Dict[str, Any]:
    """
    keep: 'oldest' | 'newest'
    Use ObjectId generation time as a stable tie-breaker.
    """
    def _ts(d):
        _id = d.get("_id")
        return _id.generation_time if isinstance(_id, ObjectId) else None

    docs_sorted = sorted(docs, key=_ts)
    if keep == "newest":
        return docs_sorted[-1]
    return docs_sorted[0]  # oldest


def ensure_unique_index(coll, key: str):
    """
    key='sample_url' => unique on [('sample',1), ('url',1)]
    key='url'        => unique on [('url',1)]
    """
    if key == "url":
        coll.create_index([("url", ASCENDING)], unique=True, name="uniq_url")
        print("✅ Ensured unique index on (url)")
    else:
        coll.create_index([("sample", ASCENDING), ("url", ASCENDING)], unique=True, name="uniq_sample_url")
        print("✅ Ensured unique index on (sample, url)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["per-sample", "global"], default="per-sample",
                    help="Dedupe within a single sample or globally")
    ap.add_argument("--key", choices=["sample_url", "url"], default="sample_url",
                    help="Duplicate definition: (sample,url) or url only")
    ap.add_argument("--sample-id", help="Required when --scope per-sample (otherwise all samples)")
    ap.add_argument("--keep", choices=["oldest", "newest"], default="oldest",
                    help="Which document to keep within each duplicate set")
    ap.add_argument("--dry-run", action="store_true", help="Preview only; do not delete")
    ap.add_argument("--limit", type=int, default=0, help="Stop after processing this many duplicate groups")
    ap.add_argument("--ensure-unique-index", action="store_true",
                    help="Create a unique index matching the dedupe key to prevent future duplicates")
    args = ap.parse_args()

    db = get_db()
    coll = db["clean_articles"]

    dup_groups = find_duplicates(coll, scope=args.scope, key=args.key, sample_id=args.sample_id)
    total_groups = len(dup_groups)

    if args.limit and args.limit > 0:
        dup_groups = dup_groups[:args.limit]

    print(f"🔎 Found {total_groups} duplicate groups; processing {len(dup_groups)} groups "
          f"(scope={args.scope}, key={args.key}, keep={args.keep}, dry_run={args.dry_run})")

    deleted = kept = 0

    for idx, group in enumerate(dup_groups, start=1):
        keep_doc = choose_to_keep(group, keep=args.keep)
        keep_id = keep_doc["_id"]
        to_delete_ids = [d["_id"] for d in group if d["_id"] != keep_id]

        print(f"\n[{idx}/{len(dup_groups)}] Group size={len(group)}")
        print(f"   Keep:   {keep_id}  (sample={keep_doc.get('sample')}, url={keep_doc.get('url')})")
        for _id in to_delete_ids:
            print(f"   Delete: {_id}")

        if not args.dry_run and to_delete_ids:
            res = coll.delete_many({"_id": {"$in": to_delete_ids}})
            deleted += res.deleted_count
            kept += 1
        else:
            kept += 1  # conceptually we keep one per group

    print("\n🏁 Done.")
    print(f"   Groups handled: {len(dup_groups)} / {total_groups}")
    print(f"   Kept (1 per group): {kept}")
    print(f"   Deleted: {deleted}")

    if args.ensure_unique_index:
        try:
            ensure_unique_index(coll, key=args.key)
        except Exception as e:
            print(f"⚠️ Could not create unique index: {e}")


if __name__ == "__main__":
    main()

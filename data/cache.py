# =============================================================================
# data/cache.py — API Response Cache (30-minute TTL)
#
# Avoids repeated yfinance/screener.in calls for the same ticker.
# Stores in memory (per session) + optional disk cache (.cache/ folder).
#
# Usage:
#   from data.cache import get_cached, set_cache, clear_cache
# =============================================================================

import os
import json
import time
import hashlib
import pickle

# ── Config ────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS  = 1800          # 30 minutes
CACHE_DIR          = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".cache"
)
USE_DISK_CACHE     = True          # Set False to use memory-only

# ── In-memory store ────────────────────────────────────────────────────────────
_memory_cache: dict = {}


def _make_key(symbol: str, data_type: str = "main") -> str:
    """Generate a consistent cache key."""
    raw = f"{symbol.upper().strip()}::{data_type}"
    return hashlib.md5(raw.encode()).hexdigest()


def _disk_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{key}.pkl")


# =============================================================================
# PUBLIC API
# =============================================================================
from typing import Optional, Dict
def get_cached(symbol: str, data_type: str = "main") -> Optional[dict]:

    """
    Return cached data for a symbol if it exists and is not expired.
    Returns None if cache miss or expired.
    """
    key = _make_key(symbol, data_type)

    # ── Memory cache first (fastest) ─────────────────────────────────────
    if key in _memory_cache:
        entry = _memory_cache[key]
        if time.time() - entry["ts"] < CACHE_TTL_SECONDS:
            return entry["data"]
        else:
            del _memory_cache[key]   # Expired

    # ── Disk cache second ─────────────────────────────────────────────────
    if USE_DISK_CACHE:
        path = _disk_path(key)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    entry = pickle.load(f)
                if time.time() - entry["ts"] < CACHE_TTL_SECONDS:
                    _memory_cache[key] = entry   # Warm memory cache
                    return entry["data"]
                else:
                    os.remove(path)   # Clean up expired disk entry
            except Exception:
                pass   # Corrupt cache file — ignore

    return None   # Cache miss


def set_cache(symbol: str, data: dict, data_type: str = "main"):
    """Store data in both memory and disk cache."""
    key   = _make_key(symbol, data_type)
    entry = {"ts": time.time(), "data": data}

    # Memory
    _memory_cache[key] = entry

    # Disk
    if USE_DISK_CACHE:
        try:
            with open(_disk_path(key), "wb") as f:
                pickle.dump(entry, f)
        except Exception:
            pass   # Non-fatal if disk write fails


def clear_cache(symbol: str = None):
    """
    Clear cache for a specific symbol or ALL symbols.
    symbol=None clears everything.
    """
    global _memory_cache

    if symbol is None:
        # Clear all
        _memory_cache = {}
        if USE_DISK_CACHE and os.path.exists(CACHE_DIR):
            for fname in os.listdir(CACHE_DIR):
                if fname.endswith(".pkl"):
                    try:
                        os.remove(os.path.join(CACHE_DIR, fname))
                    except Exception:
                        pass
        print("  Cache cleared (all symbols)")
    else:
        # Clear specific symbol
        for dtype in ["main", "screener", "history"]:
            key  = _make_key(symbol, dtype)
            _memory_cache.pop(key, None)
            if USE_DISK_CACHE:
                path = _disk_path(key)
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        print(f"  Cache cleared for {symbol}")


def cache_info() -> dict:
    """Return stats about the current cache state."""
    mem_count  = len(_memory_cache)
    disk_count = 0
    disk_size  = 0

    if USE_DISK_CACHE and os.path.exists(CACHE_DIR):
        pkl_files  = [f for f in os.listdir(CACHE_DIR) if f.endswith(".pkl")]
        disk_count = len(pkl_files)
        disk_size  = sum(
            os.path.getsize(os.path.join(CACHE_DIR, f))
            for f in pkl_files
        )

    return {
        "memory_entries": mem_count,
        "disk_entries"  : disk_count,
        "disk_size_kb"  : round(disk_size / 1024, 1),
        "ttl_minutes"   : CACHE_TTL_SECONDS // 60,
        "cache_dir"     : CACHE_DIR,
    }


def is_cached(symbol: str, data_type: str = "main") -> bool:
    """Quick check if valid cache exists without returning data."""
    return get_cached(symbol, data_type) is not None

from functools import wraps
from pathlib import Path
import sqlite3
from src.utils.parquetutils import ParquetUtils

_cache_dir = None

def set_cache_dir(path: Path):
    global _cache_dir
    _cache_dir = Path(path)
    _cache_dir.mkdir(parents=True, exist_ok=True)
    _init_db()

def _init_db():
    if _cache_dir is None: return
    db_path = _cache_dir / "raw_cache.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_index (
                raw_path TEXT PRIMARY KEY,
                cache_file TEXT,
                mtime REAL
            )
        """)

def enable_cache(func):
    """Decorator to use caching features.
    
    If the raw file is over 1 MB, it caches the processed data using Parquet.
    Subsequent calls load from cache if the raw file hasn't changed.
    """
    @wraps(func)
    def wrapper(filename, *args, **kwargs):
        if _cache_dir is None:
            return func(filename, *args, **kwargs)
        
        raw_path = Path(filename).absolute()
        try:
            mtime = raw_path.stat().st_mtime
        except OSError:
            return func(filename, *args, **kwargs)

        db_path = _cache_dir / "raw_cache.db"
        row = None
        try:
            with sqlite3.connect(db_path) as conn:
                row = conn.execute("SELECT cache_file, mtime FROM cache_index WHERE raw_path = ?", (str(raw_path),)).fetchone()
        except sqlite3.Error:
            pass

        if row:
            cache_file, cached_mtime = row
            cache_path = _cache_dir / cache_file
            if cache_path.exists() and abs(cached_mtime - mtime) < 1e-6:
                try:
                    return ParquetUtils.read_from_parquet(cache_path)
                except Exception as e:
                    print(f"Failed to read cache for {raw_path.name}: {e}")

        result = func(filename, *args, **kwargs)

        # Cache if file is > 1MB
        try:
            if raw_path.stat().st_size > 1024 * 1024:
                # MDreader.read_raw_data returns:
                # file_list, metadata, height, frequency, unique_freqs, dop_shifts, complex_signal
                file_list, metadata, height, frequency, unique_freqs, dop_shifts, complex_signal = result
                
                extension = raw_path.suffix.replace('.', '')
                # ParquetUtils.write_to_parquet appends _{extension}.parquet to filename.stem
                ParquetUtils.write_to_parquet(metadata, frequency, height, unique_freqs, dop_shifts, complex_signal, raw_path, _cache_dir, extension)
                
                cache_file = f"{raw_path.stem}_{extension}.parquet"
                with sqlite3.connect(db_path) as conn:
                    conn.execute("INSERT OR REPLACE INTO cache_index (raw_path, cache_file, mtime) VALUES (?, ?, ?)",
                                 (str(raw_path), cache_file, mtime))
        except Exception as e:
            print(f"Failed to write cache for {raw_path.name}: {e}")

        return result
    return wrapper

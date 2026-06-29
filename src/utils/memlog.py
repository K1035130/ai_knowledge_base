"""Tiny helper for pinpointing OOM causes on Render — logs peak RSS at chosen checkpoints."""

try:
    import resource  # Unix-only

    def peak_rss_mb() -> float | None:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
except ImportError:  # Windows (local dev) has no `resource` module

    def peak_rss_mb() -> float | None:
        return None


def log_rss(label: str) -> None:
    rss = peak_rss_mb()
    if rss is not None:
        print(f"[mem] {label} — peak RSS so far: {rss:.0f} MB", flush=True)

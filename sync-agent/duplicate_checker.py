"""Detect already-imported articles to avoid duplicates."""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ImportRecord:
    source_url: str
    slug: str
    path: Path
    imported_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DuplicateChecker:
    """Check and record imported article URLs.

    Uses two mechanisms:
    1. A persistent JSON state file mapping source URLs to imported paths.
    2. A scan of existing ``.rst`` files in the content directory for the
       ``Publication: <source_url>`` marker we emit on import.
    """

    SOURCE_RE = re.compile(r"^[^:\n]{1,40}:\s*(https?://\S+)", re.MULTILINE)

    def __init__(self, content_dir: Path, state_path: Path | None) -> None:
        self.content_dir = Path(content_dir)
        self.state_path = Path(state_path) if state_path else None
        self._state: list[dict[str, str]] = []
        self._load_state()

    def is_duplicate(self, source_url: str) -> bool:
        """Return ``True`` if ``source_url`` has already been imported."""
        normalised = self._normalise_url(source_url)

        # 1. Fast lookup in state file.
        for record in self._state:
            if self._normalise_url(record.get("source_url", "")) == normalised:
                logger.info("Duplicate detected from state file: %s", source_url)
                return True

        # 2. Scan existing article files for the source URL marker.
        for path in self.content_dir.glob("*.rst"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning("Could not read %s: %s", path, exc)
                continue

            for match in self.SOURCE_RE.finditer(text):
                if self._normalise_url(match.group(1)) == normalised:
                    logger.info("Duplicate detected in existing file %s: %s", path, source_url)
                    return True

        return False

    def record(self, source_url: str, slug: str, path: Path) -> None:
        """Persist metadata about a successful import."""
        self._state.append(
            {
                "source_url": source_url,
                "slug": slug,
                "path": str(path),
                "imported_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_state()

    def _load_state(self) -> None:
        if not self.state_path or not self.state_path.exists():
            return
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not load state file %s: %s", self.state_path, exc)
            return

        if isinstance(payload, dict) and "imports" in payload:
            self._state = payload["imports"]
        elif isinstance(payload, list):
            self._state = payload
        else:
            self._state = []

    def _save_state(self) -> None:
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump({"imports": self._state}, handle, indent=2, ensure_ascii=False)

    @staticmethod
    def _normalise_url(url: str) -> str:
        """Normalise a URL for comparison by removing fragments and trailing slash."""
        return url.split("#")[0].rstrip("/")

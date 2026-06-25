"""Write the converted article to the Pelican content directory."""

import logging
from pathlib import Path

from converter import RstDocument

logger = logging.getLogger(__name__)


class ArticleWriter:
    """Write :class:`RstDocument` instances as ``.rst`` files."""

    def __init__(self, content_dir: Path) -> None:
        self.content_dir = Path(content_dir)
        if not self.content_dir.exists():
            raise FileNotFoundError(f"Content directory does not exist: {self.content_dir}")
        if not self.content_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.content_dir}")

    def write(self, document: RstDocument) -> Path:
        """Write ``document`` to the content directory and return the file path."""
        filename = f"{document.date:%Y%m%d}-{document.slug}.rst"
        path = self.content_dir / filename

        if path.exists():
            raise FileExistsError(f"Article file already exists: {path}")

        path.write_text(document.render(), encoding="utf-8")
        logger.info("Wrote article to %s", path)
        return path

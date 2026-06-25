"""CLI entry point for the sync agent."""

import argparse
import logging
import sys
from pathlib import Path

# Ensure sibling modules in this directory are importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from converter import Converter
from duplicate_checker import DuplicateChecker
from fetcher import Fetcher
from parser import Parser
from writer import ArticleWriter

logger = logging.getLogger("sync_agent")


DEFAULT_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
DEFAULT_STATE_DIR = Path(__file__).resolve().parent


def _setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync-agent",
        description="Import a news or magazine article into deepavraman.com.",
    )
    parser.add_argument("url", help="Article URL to import")
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=DEFAULT_CONTENT_DIR,
        help=f"Pelican content directory (default: {DEFAULT_CONTENT_DIR})",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=DEFAULT_STATE_DIR,
        help=f"Directory where state.json is stored (default: {DEFAULT_STATE_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and convert the article but do not write a file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG level logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    _setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    source_url: str = args.url
    content_dir: Path = args.content_dir
    state_path: Path = args.state_dir / "state.json"

    logger.info("Starting sync for %s", source_url)

    try:
        duplicate_checker = DuplicateChecker(content_dir, state_path)
        if duplicate_checker.is_duplicate(source_url):
            logger.info("Skipping already imported article: %s", source_url)
            return 0

        fetcher = Fetcher()
        response = fetcher.fetch(source_url)

        parser = Parser()
        article = parser.parse(response.body, response.url)

        converter = Converter()
        document = converter.convert(article)

        if args.dry_run:
            logger.info("Dry-run output for %s:\n%s", source_url, document.render())
            return 0

        writer = ArticleWriter(content_dir)
        path = writer.write(document)
        duplicate_checker.record(document.source_url, document.slug, path)

        logger.info("Imported article: %s", path)
        return 0

    except FileExistsError as exc:
        logger.warning("Duplicate file detected: %s", exc)
        return 0
    except Exception as exc:  # noqa: BLE001 -- CLI top-level catch for graceful exit.
        logger.exception("Import failed for %s: %s", source_url, exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

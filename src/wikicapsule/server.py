"""WikiCapsule MCP Server — main entry point."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from wikicapsule.config import WikiCapsuleConfig
from wikicapsule.prompts import get_prompt, get_prompts
from wikicapsule.resources import discover_wiki_pages, read_resource
from wikicapsule.tools import register_tools
from wikicapsule.wiki import WikiManager

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the server."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def create_mcp_server(config: WikiCapsuleConfig) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        config: WikiCapsule configuration

    Returns:
        Configured FastMCP server instance
    """
    wiki = WikiManager(config)

    mcp = FastMCP("wikicapsule")

    # Register resources
    @mcp.resource("wiki://index.md")
    def get_index() -> str:
        """Auto-maintained catalog of all wiki pages."""
        return read_resource("wiki://index.md", wiki, config)

    @mcp.resource("wiki://log.md")
    def get_log() -> str:
        """Chronological append-only log of all operations."""
        return read_resource("wiki://log.md", wiki, config)

    @mcp.resource("wiki://WIKI.md")
    def get_wiki_schema() -> str:
        """Provider-agnostic schema and configuration document."""
        return read_resource("wiki://WIKI.md", wiki, config)

    @mcp.resource("wiki://wiki/{path:path}")
    def get_wiki_page(path: str) -> str:
        """Read any wiki page by path."""
        return read_resource(f"wiki://wiki/{path}", wiki, config)

    @mcp.resource("wiki://raw/{path:path}")
    def get_raw_document(path: str) -> str:
        """Read any raw source document by path."""
        return read_resource(f"wiki://raw/{path}", wiki, config)

    # Register tools
    register_tools(mcp, wiki, config)

    # Register prompts
    @mcp.prompt()
    def ingest_workflow(source_path: str, source_type: str) -> str:
        """Guide through ingesting a source document."""
        result = get_prompt("ingest_workflow", {"source_path": source_path, "source_type": source_type})
        # Return the text content of the first message
        if result.messages:
            content = result.messages[0].content
            if hasattr(content, "text"):
                return content.text
        return "Error: Could not load ingest workflow prompt"

    @mcp.prompt()
    def query_workflow(question: str) -> str:
        """Guide through querying the wiki."""
        result = get_prompt("query_workflow", {"question": question})
        if result.messages:
            content = result.messages[0].content
            if hasattr(content, "text"):
                return content.text
        return "Error: Could not load query workflow prompt"

    @mcp.prompt()
    def lint_workflow(scope: str = "quick") -> str:
        """Guide through linting the wiki."""
        result = get_prompt("lint_workflow", {"scope": scope})
        if result.messages:
            content = result.messages[0].content
            if hasattr(content, "text"):
                return content.text
        return "Error: Could not load lint workflow prompt"

    return mcp


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="WikiCapsule MCP Server")
    parser.add_argument(
        "--wiki-dir",
        type=str,
        default=os.environ.get("WIKICAPSULE_WIKI_DIR", "."),
        help="Root wiki directory (default: current directory)",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default=os.environ.get("WIKICAPSULE_TRANSPORT", "stdio"),
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("WIKICAPSULE_PORT", "8080")),
        help="Port for SSE mode (default: 8080)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("WIKICAPSULE_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML file",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    # Load configuration
    wiki_dir = Path(args.wiki_dir).expanduser().resolve()
    wiki_dir.mkdir(parents=True, exist_ok=True)

    if args.config:
        config = WikiCapsuleConfig.from_yaml(args.config)
    else:
        config = WikiCapsuleConfig.from_yaml(wiki_dir / ".wikicapsule" / "config.yaml")

    # Override with CLI args
    config.wiki_dir = wiki_dir
    config.server.transport = args.transport
    config.server.port = args.port
    config.server.log_level = args.log_level

    logger.info("WikiCapsule starting — wiki_dir=%s, transport=%s", config.wiki_dir, config.server.transport)

    # Create and run MCP server
    mcp = create_mcp_server(config)

    if config.server.transport == "sse":
        mcp.run(transport="sse", port=config.server.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

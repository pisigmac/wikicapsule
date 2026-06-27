"""MCP prompt definitions for WikiCapsule workflows."""

from __future__ import annotations

import mcp.types as types


def get_prompts() -> list[types.Prompt]:
    """Get the list of available prompts."""
    return [
        types.Prompt(
            name="ingest_workflow",
            description="Guides through the full source ingest process",
            arguments=[
                types.PromptArgument(
                    name="source_path",
                    description="Path or URL to the source document",
                    required=True,
                ),
                types.PromptArgument(
                    name="source_type",
                    description="Type of source (article/paper/book_chapter/transcript/note)",
                    required=True,
                ),
            ],
        ),
        types.Prompt(
            name="query_workflow",
            description="Guides through querying the wiki and synthesizing an answer",
            arguments=[
                types.PromptArgument(
                    name="question",
                    description="The question to answer from the wiki",
                    required=True,
                ),
            ],
        ),
        types.Prompt(
            name="lint_workflow",
            description="Guides through linting the wiki for health issues",
            arguments=[
                types.PromptArgument(
                    name="scope",
                    description="Lint scope: 'quick' or 'full'",
                    required=False,
                ),
            ],
        ),
    ]


def get_prompt(name: str, arguments: dict[str, str] | None = None) -> types.GetPromptResult:
    """Get a prompt by name with optional argument substitution.

    Args:
        name: Prompt name
        arguments: Optional argument values

    Returns:
        Prompt result with messages
    """
    args = arguments or {}

    if name == "ingest_workflow":
        source_path = args.get("source_path", "<source_path>")
        source_type = args.get("source_type", "<source_type>")

        return types.GetPromptResult(
            description="Ingest a source document into the wiki",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Let's ingest a source into the wiki. Follow these steps:

**Source**: `{source_path}` (type: {source_type})

## Step 1: Read the source
Read the source document to understand its content.

## Step 2: Discuss key insights
Identify the main points, insights, and connections to existing knowledge.

## Step 3: Create source page
Use `wiki_ingest` with:
- source_path: `{source_path}`
- source_type: `{source_type}`
- tags: [add relevant topic tags]

## Step 4: Update entity pages
Create or update relevant `entities/` pages for people, organizations, or products mentioned.

## Step 5: Update concept pages
Create or update relevant `concepts/` pages for key ideas, theories, or terms.

## Step 6: Update index
The index is auto-maintained, but verify it looks correct by reading `wiki://index.md`.

## Step 7: Log entry
The log is auto-maintained. Read `wiki://log.md` to confirm the entry was added.

Let's start with Step 1 — read and summarize the source material.""",
                    ),
                ),
            ],
        )

    if name == "query_workflow":
        question = args.get("question", "<your question>")

        return types.GetPromptResult(
            description="Query the wiki and synthesize an answer",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Let's answer this question from the wiki: **{question}**

## Step 1: Read the index
Read `wiki://index.md` to understand what the wiki contains.

## Step 2: Search for relevant pages
Use `wiki_search` with query="{question}" to find the most relevant pages.

## Step 3: Read relevant pages
Read the top 3-5 most relevant pages using their `wiki://wiki/{{path}}` URIs.

## Step 4: Synthesize an answer
Combine the information from the pages into a coherent answer with citations.
Reference specific pages like: "According to [[Page Name]]..."

## Step 5: Optionally file the answer
If the answer is valuable for future reference, use `wiki_create_page` to save it
under `explorations/` with a descriptive name.

Let's start with Step 1 — read the wiki index.""",
                    ),
                ),
            ],
        )

    if name == "lint_workflow":
        scope = args.get("scope", "quick")

        return types.GetPromptResult(
            description="Lint the wiki for health issues",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Let's run a health check on the wiki (scope: {scope}).

## Step 1: Run lint
Use `wiki_lint` with scope="{scope}" to identify issues.

## Step 2: Review contradictions
Check for any contradiction flags between pages. Read pages flagged as contradictory
and resolve or clarify the conflicting information.

## Step 3: Check for stale content
Look for pages that haven't been updated since their sources changed.
Consider updating entity/concept pages if new sources provide new information.

## Step 4: Fix orphans
Pages with no incoming wikilinks are orphans. Link them from relevant pages,
or decide they should be removed.

## Step 5: Address missing pages
Wikilinks pointing to non-existent pages indicate gaps in the knowledge base.
Create those pages or fix the links.

## Step 6: Verify index integrity
Read `wiki://index.md` and check it accurately reflects the wiki contents.

Let's start with Step 1 — run the lint check.""",
                    ),
                ),
            ],
        )

    raise ValueError(f"Unknown prompt: {name}")

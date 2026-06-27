# Product Team Meeting — Q2 Roadmap Review

**Date**: April 3, 2024
**Attendees**: Alex (PM), Jordan (Engineering Lead), Taylor (Design), Morgan (Data Science), Casey (QA)

---

## Opening

**Alex**: Okay, let's get started. We're here to finalize the Q2 roadmap. Jordan, you had some concerns about the AI search feature timeline?

**Jordan**: Yeah. The initial estimate was 3 weeks, but after digging into the vector DB setup and embedding pipeline, we're looking at closer to 6. The sentence-transformers integration is straightforward, but the hybrid search ranking needs more R&D.

**Taylor**: From the design side, the search results page is ready. I'm more worried about the empty states — what does the UI look like before any documents are ingested?

**Alex**: Good point. Morgan, can we get a default welcome experience that guides users through their first ingest?

**Morgan**: Absolutely. We can ship a pre-built onboarding flow — sample data plus a guided tour. I'd estimate 3 days of work.

## AI Search Feature Deep Dive

**Jordan**: Let me walk through the technical approach. We're using SQLite FTS5 for keyword search and sentence-transformers for semantic search. The hybrid ranking uses reciprocal rank fusion.

**Morgan**: Have we benchmarked the embedding model? all-MiniLM-L6-v2 is 384 dimensions — fast but might miss nuance for technical queries.

**Jordan**: We did a quick eval. On our internal test set, it achieves 0.82 recall@5. That's good enough for MVP. We can swap in a larger model later without changing the interface.

**Casey**: What about testing? We need to verify search results are deterministic.

**Jordan**: The BM25 component is deterministic. Vector search has minor variance due to floating point, but we set numpy to deterministic mode in tests.

**Alex**: Decision: 6-week timeline for AI search, with a 2-week checkpoint for the hybrid ranking. Jordan, send me the detailed breakdown by EOD.

## Onboarding Experience

**Taylor**: I have three concepts for the empty state. [Shares screen]

Option A: Simple getting started card with three steps.
Option B: Interactive demo with pre-loaded sample wiki.
Option C: Video tutorial embedded in the UI.

**Morgan**: Option B aligns with what I was thinking. We can ship sample data — a few markdown files covering different content types — so users see value immediately.

**Alex**: Let's go with B. Taylor, can you have the mockups ready by Friday?

**Taylor**: Yep.

## Performance Budget

**Jordan**: We agreed on these targets:
- Search latency: <500ms p99
- Ingest time: <5s per document
- Query response: <2s end-to-end

**Casey**: For the performance tests, I need representative data. How many documents should the test corpus have?

**Jordan**: Start with 100. That's a realistic medium-size wiki. We'll also do a stress test at 10K.

**Alex**: Great. Casey, add the performance tests to the CI pipeline. Fail the build if we exceed the budget.

## Action Items

| Owner | Task | Due |
|-------|------|-----|
| Jordan | Detailed AI search breakdown | April 3 |
| Taylor | Onboarding mockups (Option B) | April 5 |
| Morgan | Sample data creation | April 8 |
| Casey | Performance test suite | April 12 |
| Alex | Finalize roadmap doc | April 4 |

## Closing

**Alex**: Good discussion, everyone. The Q2 roadmap is shaping up nicely. Our two big bets are AI search and onboarding. Let's execute. Next check-in is Monday at 10am.

**All**: Thanks, Alex.

---
*Meeting adjourned at 11:35am*

# Issue tracker: Local Markdown

Issues and PRDs for this project live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- Implementation issues live in `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is recorded as a `Status:` line near the top of each issue file
- Execution type is recorded as a `Type:` line: `AFK` for implementable work, `HITL` for work requiring human decisions or hands-on evaluation
- Comments and conversation history may be appended under a `## Comments` heading

## Current feature

- Product PRD: `.scratch/ai-career-coach-product/PRD.md`
- Real-time voice V0 issues: `.scratch/realtime-voice-v0/issues/`

## Publishing and fetching

- To publish an issue, create the next numbered Markdown file in the feature's `issues/` directory.
- To fetch an issue, read the referenced Markdown file directly.

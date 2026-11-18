# Agent Instructions

## ⚠️ CRITICAL: Session Start Protocol — READ BEFORE ANY OTHER ACTION
At the **very start of every session** (before any tool calls or responses), you **MUST**:
1. Read `/workspaces/stamps-web-app/memory-bank/index.md`
2. Follow the instructions in index.md for which memory-bank files to read
3. Update `activeContext.md` with your current task status when prompted

**Failure to do this will result in missing critical context and producing incorrect work.**

## Workspace
- Working directory: `/workspaces/stamps-web-app`
- Memory-bank location: `/workspaces/stamps-web-app/memory-bank/`

## Language and GitHub

- **GitHub issue titles are also branch names.** Issue creation lowercases the
  title and replaces spaces with dashes, so write the title naturally in English
  (spaces are fine, no need to pre-kebab-case it) but keep it short and free of
  punctuation a branch name cannot hold (`:` `,` `!` `/` quotes). Do not add the
  issue number or the type yourself — the tooling that creates the branch adds
  both (`212-feature-stamps-manager-add-issues`).
- **Every GitHub operation is in English** — issue titles and descriptions,
  commit messages, PR titles and descriptions, review comments.
- **GitHub operations are not authorized.** Never create, edit, close or comment
  on issues, PRs or releases, and never push. Suggesting issue titles,
  descriptions and commit messages is allowed and expected.
- **Code is exclusively in English** — identifiers, comments, docstrings, log
  messages, test names, template/UI strings keys (translations themselves may be
  in any language).
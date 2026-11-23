# md-toc

Generate a Markdown table of contents from the headings in a Markdown file.
Anchors follow GitHub's slug rules: lowercase, HTML and punctuation removed,
spaces replaced with hyphens, and duplicate headings suffixed `-1`, `-2`, and so
on. Headings inside fenced code blocks are ignored, as are setext headings.

## Usage

```sh
python3 md_toc.py README.md
cat README.md | python3 md_toc.py --max-depth 2
python3 md_toc.py docs/guide.md > toc.md
```

Example output:

```markdown
- [Project](#project)
  - [Install & Run](#install--run)
    - [Use `--fast` mode](#use---fast-mode)
```

Inline code, emphasis, links, and images are reduced to their visible text
before the anchor is computed. `--max-depth N` limits the heading levels
included (1-6, default 6). Input is a file path or `-` (default) for stdin.

Exit codes: `0` success (including a document with no headings, which prints
nothing), `2` for unreadable input or an invalid depth.

## Test

```sh
python3 md_toc.py --self-test
```

The self-test covers nested headings, duplicate anchors, inline formatting,
punctuation, code-fence exclusion, depth limiting, and empty input.

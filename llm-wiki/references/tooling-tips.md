# Tooling Tips

Practical notes for working with a wiki in this layout.

Everything here is **optional**. The skill's own scripts need nothing but CPython 3.10 or later
and the standard library, and a wiki is plain Markdown on disk — no application has to be
installed or running for any operation to work. What follows is about making the wiki pleasant
to read and easy to feed, not about making it function.

## Obsidian setup

Obsidian is the most convenient reader for a wiki this shape, because it resolves `[[wikilinks]]`
and draws the graph.

### Settings worth changing

1. **Attachment folder** — Settings → Files and links → "Attachment folder path" → `raw/assets/`.
2. **New file location** — Settings → Files and links → "Default location for new notes" →
   `wiki/concepts/`.
3. **Download attachments hotkey** — Settings → Hotkeys → search "Download attachments" → bind
   it. After clipping an article, one keystroke pulls its images local.

### Plugins worth having

- **Obsidian Web Clipper** (browser extension) — turns a web page into Markdown in your vault.
  Configure it to save into `raw/sources/`.
- **Dataview** (optional) — queries front matter, so you can build live tables of pages by tag,
  date, or source count. Useful once the wiki outgrows a readable `index.md`.
- **Marp** (optional) — renders wiki content as slides.

### Graph view

`Ctrl+G` is the fastest way to see the wiki's actual shape:

- A dense hub is a well-connected concept page.
- An isolated node is an orphan — it needs an inbound link, or it needs deleting.
  `lint_wiki.py`'s `orphan-pages` pass finds these without opening Obsidian at all, and it does
  not count the index as a link: a catalog entry is not a citation.
- A cluster is a sub-topic that has earned a folder-split under `wiki/concepts/`.

## Filing corrections

There is no plugin and no viewer. A correction is a file you write in `audit/`, and
`references/audit-guide.md` has the format. Obsidian is a perfectly good editor for writing one:
select the wrong text, copy it into `anchor_text`, and grab the surrounding lines for
`anchor_before` and `anchor_after`.

`python3 scripts/audit_review.py <wiki-root> --open` then lists everything outstanding, grouped
by target and ordered by severity, so you can see the backlog without reading each file.

## Capturing sources

1. Install the Web Clipper from [obsidian.md/clipper](https://obsidian.md/clipper).
2. Point its template at `raw/sources/`.
3. Clip, download the images, and the file is ready for `ingest`.

For a page the clipper cannot handle — paywalled, heavily dynamic — copy the main text by hand
into `raw/sources/<slug>.md`. For anything too large to copy at all, write a pointer file in
`raw/refs/` instead; the raw file policy in `SKILL.md` has the format.

## Semantic search for a large wiki

Once the wiki passes roughly a hundred pages, scanning `wiki/index.md` stops being the fast path.
[qmd](https://github.com/tobi/qmd) is a local hybrid BM25-plus-vector search over Markdown:

```bash
pip install qmd
qmd collection add wiki/ --name my-wiki
qmd embed
qmd query "what are the tradeoffs of RAG versus a compiled wiki" --collection my-wiki
```

It also exposes an MCP server, so an agent can query it as a tool. This is genuinely optional:
nothing in the skill reads a qmd index, and a wiki with no index built still works exactly as
before.

## Charts and generated figures

For a quantitative page, have the LLM write a matplotlib script, run it, and save the **image**
into `raw/assets/`:

```python
plt.savefig("raw/assets/rag-latency-comparison.png")
```

Embed it in a page with `![[rag-latency-comparison.png]]`.

Keep the script itself outside the wiki. `raw/` holds source material and assets a page cites;
a build script is neither, and a wiki that accumulates code becomes a repository with a wiki
inside it rather than a wiki.

## Slides

Marp reads a Markdown file with `marp: true` in its front matter and slides split on `---`.
Install the Obsidian Marp plugin to preview and export without leaving the vault. Keep the deck
outside `wiki/`: it is an output, not a page, and `lint` will ask why it is not in the index.

## Git

Tracking the wiki in Git is a choice, not a requirement, and no operation assumes either way.
When you do track it you get version history per page, branches for speculative research
directions, and corrections as first-class history — "who said this was wrong, and when" becomes
a `git log` question.

```bash
git add .
git commit -m "ingest: three papers on attention mechanisms"
```

Keep large files out: PDFs over 10 MB, full-resolution images, video, model weights. Use the raw
file policy — a pointer in `raw/refs/`, never a copy.

If the wiki lives **inside** another project's repository, decide deliberately whether it is
tracked with that project or ignored by it. Both work. `scripts/project_binding.py` reports which
situation you are in, and reports tracking as unknown rather than as zero when the project is not
a Git repository at all — a distinction worth keeping, because "nothing is tracked" and "there is
nothing to track with" are different facts.

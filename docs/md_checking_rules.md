# Markdown Checking Rules

## Rules

- Headers must progress sequentially down (H1→H2→H3→H4), no skipping
- Jumping back up is allowed (H4→H2)
- Space required after `#` symbols: `## Heading` not `##Heading`

## Examples

**Level skip** ❌
```markdown
## Section
#### Subsection  # skips H3
```

**Missing space** ❌
```markdown
###Quick Answer
```

## Validation

```bash
python src/check_md_hierarchy.py docs/README.md
python src/check_md_hierarchy.py docs/*.md
```

Exits 0 if clean, 1 if violations found. Ignores code blocks.

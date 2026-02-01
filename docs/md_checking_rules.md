# Markdown Checking Rules

Rules for validating markdown files before PDF conversion.

## Heading Hierarchy Rules

1. **No level skipping**: Headers must progress sequentially (H1→H2→H3→H4)
   - ✅ Valid: H1 → H2 → H3
   - ❌ Invalid: H1 → H3 (skips H2)
   - ❌ Invalid: H2 → H4 (skips H3)

2. **Heading spacing**: All headers must have a space after the `#` symbols
   - ✅ Valid: `## Heading`
   - ❌ Invalid: `##Heading`

3. **Level jumping up is allowed**: You can jump from H4 back to H2
   - ✅ Valid: H4 → H2 (closing subsections)

## Common Violations

### Skipping levels after section headers
```markdown
## Q14 — Vector Search

#### Pretrained Models  ❌ Skips H3
```

**Fix:**
```markdown
## Q14 — Vector Search

### Pretrained Models  ✅ Correct hierarchy
```

### Missing spaces
```markdown
###Quick Answer  ❌ No space after ###
```

**Fix:**
```markdown
### Quick Answer  ✅ Has space
```

## Validation Script

Use `src/check_md_hierarchy.py` to validate markdown files before conversion.

```bash
# Check a single file
python src/check_md_hierarchy.py docs/README.md

# Check multiple files
python src/check_md_hierarchy.py docs/*.md
```

The script will:
- Report heading hierarchy violations (level skips)
- Detect missing spaces after `#` symbols
- Ignore code blocks (between ``` markers)
- Exit with code 0 if all checks pass, 1 if violations found

## Conversion Tools

### PDF Conversion
```bash
python src/convert_md_to_pdf.py docs/README.md
```

### LaTeX Conversion
```bash
python src/convert_md_to_pdf.py --format tex docs/README.md
```

The LaTeX converter supports:
- Headings (H1-H4)
- Bold and italic text
- Inline code and code blocks
- Math equations ($...$ inline, $$...$$ display)
- Lists (ordered and unordered)
- Links
- Tables (markdown pipe tables with alignment)

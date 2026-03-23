#!/usr/bin/env bash
set -euo pipefail

# Usage: ./move_md.sh <directory>
# Copies the .md file from <directory> one level up and updates image links.

dir="${1:?Usage: $0 <directory>}"
dir="${dir%/}"  # strip trailing slash

md_file=$(find "$dir" -maxdepth 1 -name "*.md" | head -1)
if [[ -z "$md_file" ]]; then
    echo "No .md file found in $dir" >&2
    exit 1
fi

dest="$(dirname "$dir")/$(basename "$md_file")"
cp "$md_file" "$dest"

# Update image links: ![...](filename.png) -> ![...](dir/filename.png)
# Matches any ![...](path) where path does not already contain a slash
dirname_only="$(basename "$dir")"
sed -i '' "s|!\[\([^]]*\)\](\([^/)][^)]*\))|![\1](${dirname_only}/\2)|g" "$dest"

echo "Created: $dest"
echo "Image links updated: $(grep -c '!\[' "$dest")"

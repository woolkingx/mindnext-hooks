#!/bin/bash
# Sync local wiki/ directory to GitHub Wiki

WIKI_REPO="https://github.com/woolkingx/mindnext-hooks.wiki.git"
TEMP_DIR="/tmp/mindnext-wiki-sync"

echo "🔄 Syncing wiki to GitHub..."

# Clone or update wiki repo
if [ -d "$TEMP_DIR" ]; then
    cd "$TEMP_DIR"
    git pull
else
    git clone "$WIKI_REPO" "$TEMP_DIR"
    cd "$TEMP_DIR"
fi

# Copy all markdown files from local docs/
cp ../hooks/docs/*.md ./

# Commit and push
git add .
git commit -m "📚 Sync wiki from local repository - $(date)"
git push

echo "✅ Wiki sync completed!"

# Cleanup
cd ..
rm -rf "$TEMP_DIR"
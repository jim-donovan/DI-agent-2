#!/bin/bash
# Quick script to unstage files and add patterns to .gitignore

echo "🔧 Unstaging files and updating .gitignore"
echo "=========================================="

# Unstage all currently staged files
echo ""
echo "📤 Unstaging any staged files..."
git reset HEAD .

# Add patterns to .gitignore
echo ""
echo "📝 Adding patterns to .gitignore..."

cat >> .gitignore << 'EOF'

# Auto-generated ignore patterns ($(date))
# Test infrastructure
tests/
pytest.ini
test_*.py
.coverage
coverage.json
.pytest_cache/

# Documentation (local only)
CLAUDE.md
*.skills.md
PROJECT_STRUCTURE.md
METADATA_CLEANING.md

# PDFs
*.pdf

# Archive
archive/

# Temp/downloads
gradio_downloads/

# Development scripts
update_huggingface.sh
manage_gitignore.py
unstage_and_ignore.sh

# Test execution files
test_executor_leak*.py
test_cleanup_methods.py
EOF

echo "✅ Patterns added to .gitignore"

# Remove files from git cache that are now ignored
echo ""
echo "🗑️  Removing ignored files from git cache..."

# Remove test files from cache if tracked
git rm --cached -r tests/ 2>/dev/null || true
git rm --cached pytest.ini 2>/dev/null || true
git rm --cached test_*.py 2>/dev/null || true
git rm --cached .coverage 2>/dev/null || true
git rm --cached coverage.json 2>/dev/null || true
git rm --cached CLAUDE.md 2>/dev/null || true
git rm --cached *.skills.md 2>/dev/null || true
git rm --cached *.pdf 2>/dev/null || true
git rm --cached -r archive/ 2>/dev/null || true
git rm --cached -r gradio_downloads/ 2>/dev/null || true
git rm --cached test_executor_leak*.py 2>/dev/null || true
git rm --cached test_cleanup_methods.py 2>/dev/null || true

echo "✅ Removed ignored files from cache"

# Show current status
echo ""
echo "📊 Current status:"
git status --short

echo ""
echo "✅ Done!"
echo ""
echo "💡 Next steps:"
echo "   1. Review changes: git status"
echo "   2. Stage files: git add <files>"
echo "   3. Commit: git commit -m 'Update message'"
echo "   4. Push: git push origin main"

#!/bin/bash
# Script to update HuggingFace Space with core application files

echo "🚀 Updating HuggingFace Space: jimbrodonovan/DI-agent-2"
echo ""

# Step 1: Stage core application files
echo "📦 Staging core application files..."
git add app.py
git add ui.py
git add requirements.txt
git add README.md

# Step 2: Stage agent files (required for app to run)
echo "🤖 Staging agent files..."
git add agent_base.py
git add agent_ocr_engine.py
git add vision_ocr_agent.py
git add corruption_agent.py
git add content_formatting_agent.py
git add checker_agent.py
git add summary_agent.py
git add excel_formatting_agent.py
git add excel_ingestion_agent.py
git add excel_structure_agent.py
git add vision_recommendation_agent.py

# Step 3: Stage supporting files
echo "📚 Staging supporting files..."
git add config.py
git add utils.py
git add processor_optimized.py
git add corruption_detector.py
git add summary_generator.py
git add api_client.py
git add unified_client.py

# Step 4: Stage evaluation files
echo "🔍 Staging evaluation files..."
git add evaluation/

# Step 5: Stage prompts directory
echo "💬 Staging prompts directory..."
git add prompts/

# Step 6: Update .gitignore
echo "🚫 Updating .gitignore..."
git add .gitignore

# Step 7: Remove deleted files
echo "🗑️  Removing deleted files..."
git rm checker_agent_old.py 2>/dev/null || true

# Step 8: Show what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short

echo ""
echo "✅ Files staged! Ready to commit and push."
echo ""
echo "Next steps:"
echo "1. Review the changes above"
echo "2. Run: git commit -m 'Update application with new features and improvements'"
echo "3. Run: git push huggingface main"
echo ""
echo "⚠️  Note: Tests, documentation, and temporary files are excluded from this update"

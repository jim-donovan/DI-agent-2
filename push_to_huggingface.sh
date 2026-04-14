#!/bin/bash
# Simple script to push updates to HuggingFace Space

set -e  # Exit on error

echo "🚀 Pushing to HuggingFace Space"
echo "================================"
echo ""

# Show what will be committed
echo "📋 Files that will be pushed:"
echo ""
git status --short
echo ""

# Prompt for confirmation
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Cancelled"
    exit 1
fi

# Stage all changes (respects .gitignore)
echo ""
echo "📦 Staging changes..."
git add .

# Show what's staged
echo ""
echo "✅ Staged files:"
git status --short
echo ""

# Get commit message
echo "💬 Enter commit message (or press Enter for default):"
read commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Update application with new features and improvements"
fi

# Commit
echo ""
echo "💾 Committing with message: '$commit_msg'"
git commit -m "$commit_msg"

# Push to HuggingFace
echo ""
echo "🌐 Pushing to HuggingFace Space..."
git push huggingface main

echo ""
echo "✅ Successfully pushed to HuggingFace!"
echo ""
echo "🔗 View your space at: https://huggingface.co/spaces/jimbrodonovan/DI-agent-2"
echo ""
echo "⏰ Note: It may take 1-2 minutes for HuggingFace to rebuild the space"

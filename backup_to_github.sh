#!/bin/bash
# Script to backup ClimateAI project to GitHub
# NOTE: You will need to provide your GitHub repository details

echo "==========================================="
echo "ClimateAI Project Backup to GitHub"
echo "==========================================="
echo ""

echo "Before proceeding with the backup, you need to:"
echo ""
echo "1. Create a new repository on GitHub named 'climateAI'"
echo "2. Get the repository URL (e.g., https://github.com/YOUR_USERNAME/climateAI.git)"
echo "3. Have your GitHub personal access token ready (if using authentication)"
echo ""

read -p "Enter your GitHub repository URL: " REPO_URL

# Add remote origin
git remote add origin $REPO_URL

echo ""
echo "Remote origin added. Current status:"
git remote -v

echo ""
echo "Attempting to set upstream branch and push..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully backed up ClimateAI project to GitHub!"
    echo ""
    echo "Repository URL: $REPO_URL"
    echo "Branch: main"
    echo "Files backed up: $(git ls-files | wc -l)"
    echo "Last commit message: $(git log -1 --pretty=format:%s)"
else
    echo ""
    echo "❌ GitHub push failed. This may happen if:"
    echo "   - The repository URL is incorrect"
    echo "   - You don't have push permissions"
    echo "   - Authentication is required (use HTTPS with personal access token or SSH keys)"
    echo ""
    echo "To troubleshoot, you can:"
    echo "1. Check your repository URL: git remote -v"
    echo "2. Verify authentication: git ls-remote origin"
    echo "3. Retry with different authentication method (SSH vs HTTPS)"
fi

echo ""
echo "==========================================="
echo "Backup Process Completed"
echo "==========================================="

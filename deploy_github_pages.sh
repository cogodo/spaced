#!/bin/bash

# Exit if any command fails
set -e

echo "🚀 Starting GitHub Pages deployment..."

# Navigate to the project root
# Uncomment if script is not run from project root
# cd $(dirname "$0")

# Ensure we have the latest code from the main branch
echo "📥 Pulling latest changes from main branch..."
git checkout main
git pull origin main

# Clean up any previous build
echo "🧹 Cleaning up previous build..."
rm -rf build/web

# Build the Flutter web app in release mode
echo "🏗️ Building Flutter web app in release mode..."
flutter clean
flutter build web --release

# Create gh-pages branch if it doesn't exist
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "🔧 Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
    git commit --allow-empty -m "Initial gh-pages commit"
    git checkout main
fi

# Switch to gh-pages branch
echo "🔄 Switching to gh-pages branch..."
git checkout gh-pages

# Remove existing files but keep .git directory
find . -maxdepth 1 ! -name '.git' ! -name '.' ! -name 'build' -exec rm -rf {} \;

# Copy the build files
echo "📋 Copying build files..."
cp -R build/web/* .

# Create .nojekyll file to bypass Jekyll processing
touch .nojekyll

# Add and commit the changes
echo "💾 Committing changes..."
git add -A
git commit -m "Deploy to GitHub Pages: $(date)"

# Push to the gh-pages branch
echo "📤 Pushing to gh-pages branch..."
git push origin gh-pages

# Return to main branch
echo "🔙 Switching back to main branch..."
git checkout main

echo "✅ Deployment complete! Your app should be available at https://getspaced.app/"
echo "Note: If this is your first deployment, it may take a few minutes for GitHub Pages to build your site." 
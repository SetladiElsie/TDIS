# TDIS - Render Deployment Script
# This script prepares and pushes your code to Git for Render deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TDIS - Render Deployment Preparation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "❌ Git repository not initialized" -ForegroundColor Red
    Write-Host "Run: git init" -ForegroundColor Yellow
    exit 1
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Found uncommitted changes" -ForegroundColor Yellow
    Write-Host ""
    
    # Show what will be committed
    Write-Host "Files to be committed:" -ForegroundColor Cyan
    git status --short
    Write-Host ""
    
    # Ask for confirmation
    $confirm = Read-Host "Commit these changes? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "❌ Deployment cancelled" -ForegroundColor Red
        exit 1
    }
    
    # Get commit message
    $message = Read-Host "Enter commit message (default: 'Ready for Render deployment')"
    if (-not $message) {
        $message = "Ready for Render deployment"
    }
    
    # Stage and commit
    Write-Host ""
    Write-Host "📦 Staging files..." -ForegroundColor Cyan
    git add .
    
    Write-Host "💾 Committing..." -ForegroundColor Cyan
    git commit -m $message
    
    Write-Host "✅ Changes committed" -ForegroundColor Green
} else {
    Write-Host "✅ No uncommitted changes" -ForegroundColor Green
}

Write-Host ""

# Check for remote
$remote = git remote -v
if (-not $remote) {
    Write-Host "⚠️  No Git remote configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To add a remote:" -ForegroundColor Cyan
    Write-Host "  git remote add origin https://github.com/yourusername/tdis.git" -ForegroundColor White
    Write-Host ""
    $skipPush = Read-Host "Skip push for now? (y/n)"
    if ($skipPush -ne "y") {
        exit 1
    }
} else {
    Write-Host "🚀 Git remote configured:" -ForegroundColor Green
    git remote -v
    Write-Host ""
    
    # Ask to push
    $push = Read-Host "Push to remote? (y/n)"
    if ($push -eq "y") {
        $branch = git branch --show-current
        Write-Host ""
        Write-Host "📤 Pushing to $branch..." -ForegroundColor Cyan
        git push origin $branch
        Write-Host "✅ Pushed successfully!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Deploy via Render Dashboard" -ForegroundColor Yellow
Write-Host "  1. Go to: https://dashboard.render.com" -ForegroundColor White
Write-Host "  2. Click 'New +' → 'Blueprint'" -ForegroundColor White
Write-Host "  3. Connect your repository" -ForegroundColor White
Write-Host "  4. Render will detect render.yaml" -ForegroundColor White
Write-Host "  5. Click 'Apply' to deploy all services" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Deploy via Render MCP (Kiro)" -ForegroundColor Yellow
Write-Host "  In Kiro chat, type:" -ForegroundColor White
Write-Host "  'Deploy my TDIS application to Render'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 3: Manual Service Creation" -ForegroundColor Yellow
Write-Host "  See: RENDER_DEPLOY_NOW.md (Method 2)" -ForegroundColor White
Write-Host ""
Write-Host "📚 Full deployment guide: RENDER_DEPLOY_NOW.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Estimated deployment time: 30-45 minutes" -ForegroundColor White
Write-Host "Estimated monthly cost: $21 (Starter plan)" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

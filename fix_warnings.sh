#!/bin/bash

# Comprehensive fix script for RAG Web Interface warnings
echo "🔧 Fixing RAG Web Interface Warnings..."
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Function to log with timestamp
log_fix() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/fix_warnings.log
}

log_fix "🚀 Starting comprehensive warning fixes"

# ==============================================
# 1. Fix Python/Backend Issues
# ==============================================

log_fix "🐍 Fixing Python/Backend Issues..."

# Update pip in backend virtual environment
log_fix "📦 Updating pip in backend virtual environment..."
cd web_interface/backend
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip 2>&1 | tee -a ../../logs/pip_upgrade.log
    log_fix "✅ Backend pip updated"
else
    log_fix "⚠️  Backend virtual environment not found"
fi

# Update pip in main environment (if exists)
cd ../..
if [ -f "requirements.txt" ]; then
    log_fix "📦 Updating pip in main environment..."
    pip install --upgrade pip 2>&1 | tee -a logs/pip_upgrade_main.log
    log_fix "✅ Main environment pip updated"
fi

# ==============================================
# 2. Fix Frontend/npm Issues
# ==============================================

log_fix "🎨 Fixing Frontend/npm Issues..."

cd web_interface/frontend

# Backup package-lock.json
log_fix "💾 Creating backup of package-lock.json..."
cp package-lock.json package-lock.json.backup

# Update npm itself
log_fix "📦 Updating npm..."
npm install -g npm@latest 2>&1 | tee -a ../../logs/npm_update.log

# Try to fix vulnerabilities with npm audit fix (non-breaking first)
log_fix "🔒 Attempting to fix npm vulnerabilities (safe fixes)..."
npm audit fix 2>&1 | tee -a ../../logs/npm_audit_safe.log

# Check remaining vulnerabilities
log_fix "📊 Checking remaining vulnerabilities..."
REMAINING_VULNS=$(npm audit --json 2>/dev/null | grep -o '"vulnerabilities":[0-9]*' | cut -d':' -f2 || echo "0")

if [ "$REMAINING_VULNS" -gt 0 ]; then
    log_fix "⚠️  $REMAINING_VULNS vulnerabilities remain after safe fixes"
    log_fix "💡 Manual intervention may be needed for some vulnerabilities"
    
    # Log detailed audit for manual review
    log_fix "📋 Saving detailed audit report..."
    npm audit 2>&1 | tee ../../logs/npm_audit_detailed.log
    
    # Try specific package updates for known issues
    log_fix "🔧 Attempting specific package updates..."
    
    # Update specific vulnerable packages if they exist
    if npm list postcss >/dev/null 2>&1; then
        log_fix "🔄 Updating postcss..."
        npm install postcss@latest 2>&1 | tee -a ../../logs/package_updates.log
    fi
    
    if npm list prismjs >/dev/null 2>&1; then
        log_fix "🔄 Updating prismjs..."
        npm install prismjs@latest 2>&1 | tee -a ../../logs/package_updates.log
    fi
    
else
    log_fix "✅ All npm vulnerabilities resolved with safe fixes!"
fi

# ==============================================
# 3. Clean up and optimize
# ==============================================

log_fix "🧹 Cleaning up and optimizing..."

# Clear npm cache
log_fix "🗑️  Clearing npm cache..."
npm cache clean --force 2>&1 | tee -a ../../logs/cleanup.log

# Remove node_modules and reinstall if there were issues
if [ "$REMAINING_VULNS" -gt 5 ]; then
    log_fix "🔄 Performing clean reinstall due to remaining vulnerabilities..."
    rm -rf node_modules
    npm install 2>&1 | tee -a ../../logs/clean_install.log
    log_fix "✅ Clean reinstall completed"
fi

# ==============================================
# 4. Verification
# ==============================================

log_fix "✅ Running verification checks..."

cd ../..

# Check backend dependencies
log_fix "🔍 Verifying backend dependencies..."
cd web_interface/backend
source venv/bin/activate
pip check 2>&1 | tee -a ../../logs/backend_verification.log
BACKEND_STATUS=$?

# Check frontend dependencies
log_fix "🔍 Verifying frontend dependencies..."
cd ../frontend
npm audit --audit-level=high 2>&1 | tee -a ../../logs/frontend_verification.log
FRONTEND_STATUS=$?

cd ../..

# ==============================================
# 5. Summary Report
# ==============================================

log_fix "📊 Generating summary report..."

echo ""
echo "============================================"
echo "🎯 RAG Web Interface Warning Fixes Summary"
echo "============================================"
echo ""

if [ $BACKEND_STATUS -eq 0 ]; then
    echo "✅ Backend: All dependencies clean"
else
    echo "⚠️  Backend: Some dependency issues remain"
fi

FINAL_VULNS=$(cd web_interface/frontend && npm audit --json 2>/dev/null | grep -o '"vulnerabilities":[0-9]*' | cut -d':' -f2 || echo "unknown")
echo "🔒 Frontend: $FINAL_VULNS vulnerabilities remaining"

echo ""
echo "📋 Log files created:"
echo "   - logs/fix_warnings.log (main log)"
echo "   - logs/pip_upgrade.log (pip updates)"
echo "   - logs/npm_audit_safe.log (npm safe fixes)"
echo "   - logs/npm_audit_detailed.log (detailed audit)"
echo "   - logs/package_updates.log (package updates)"
echo "   - logs/cleanup.log (cleanup operations)"
echo ""

if [ "$FINAL_VULNS" != "0" ] && [ "$FINAL_VULNS" != "unknown" ]; then
    echo "⚠️  REMAINING ACTIONS NEEDED:"
    echo "   1. Review logs/npm_audit_detailed.log"
    echo "   2. Consider running 'npm audit fix --force' (may cause breaking changes)"
    echo "   3. Update React and related packages to latest stable versions"
    echo ""
fi

echo "💡 Next steps:"
echo "   1. Test the web interface: ./start_web_interface.sh"
echo "   2. Review all log files for any remaining issues"
echo "   3. Consider updating major dependencies during next maintenance window"
echo ""

log_fix "🏁 Warning fix process completed"
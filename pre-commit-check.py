#!/usr/bin/env python3
"""
Pre-commit security check for GitHub MCP Connector
Prevents accidentally committing secrets or sensitive data
"""

import os
import re
import sys
from pathlib import Path

# Patterns that should never be committed
DANGEROUS_PATTERNS = [
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub Personal Access Tokens
    r'GITHUB_TOKEN\s*=\s*["\']?ghp_[a-zA-Z0-9]{36}',  # Token assignments
    # Note: We don't flag placeholder text like "your_github_token_here" 
    # since that's meant to be in example files
]

# Files that should be checked
CHECKABLE_EXTENSIONS = {'.py', '.json', '.md', '.txt', '.yml', '.yaml', '.env'}

# Files that should never be committed
FORBIDDEN_FILES = {
    '.env',
    '.env.local', 
    '.env.production',
    'claude_desktop_config.json',  # Real config (only .example should be committed)
    'mcp_server_config.json',      # Real config (only .example should be committed)
}

def check_file_for_secrets(file_path):
    """Check a single file for dangerous patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        issues = []
        for pattern in DANGEROUS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'pattern': pattern,
                    'match': match.group()
                })
        
        return issues
    except Exception as e:
        print(f"Warning: Could not check {file_path}: {e}")
        return []

def check_forbidden_files():
    """Check for files that should never be committed"""
    issues = []
    for forbidden_file in FORBIDDEN_FILES:
        if Path(forbidden_file).exists():
            issues.append(forbidden_file)
    return issues

def main():
    """Run pre-commit security checks"""
    print("🔍 Running pre-commit security checks...")
    
    issues_found = False
    
    # Check for forbidden files
    forbidden = check_forbidden_files()
    if forbidden:
        print("\n❌ FORBIDDEN FILES DETECTED:")
        for file_path in forbidden:
            print(f"   → {file_path}")
        print("\n   These files contain secrets and should not be committed!")
        print("   Add them to .gitignore or remove them from staging.")
        issues_found = True
    
    # Check all relevant files for secret patterns
    secret_issues = []
    for file_path in Path('.').rglob('*'):
        if (file_path.is_file() and 
            file_path.suffix in CHECKABLE_EXTENSIONS and
            not any(part.startswith('.') for part in file_path.parts[1:])):  # Skip hidden dirs
            
            issues = check_file_for_secrets(file_path)
            secret_issues.extend(issues)
    
    if secret_issues:
        print("\n❌ POTENTIAL SECRETS DETECTED:")
        for issue in secret_issues:
            print(f"   → {issue['file']}:{issue['line']} - {issue['match']}")
        print("\n   Remove these secrets before committing!")
        issues_found = True
    
    # Check that example files exist
    required_examples = [
        'env.example',
        'claude_desktop_config.example.json',
        'mcp_server_config.example.json'
    ]
    
    missing_examples = []
    for example_file in required_examples:
        if not Path(example_file).exists():
            missing_examples.append(example_file)
    
    if missing_examples:
        print("\n⚠️  MISSING EXAMPLE FILES:")
        for file_path in missing_examples:
            print(f"   → {file_path}")
        print("\n   Create these example files for sharing configurations safely.")
    
    if issues_found:
        print("\n🚫 COMMIT BLOCKED - Fix security issues above!")
        print("\n💡 Tips:")
        print("   → Use .env files for secrets (already in .gitignore)")
        print("   → Only commit .example files, not real configs")
        print("   → Replace any real tokens with placeholders")
        return 1
    else:
        print("\n✅ Security checks passed!")
        print("   → No secrets detected")
        print("   → No forbidden files found")
        print("   → Safe to commit!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
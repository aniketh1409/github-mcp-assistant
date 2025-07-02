#!/usr/bin/env python3
"""
Test script for GitHub MCP Connector
Run this to verify your setup is working correctly.
"""

import os
import sys
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import github
        print("  ✅ PyGithub installed")
    except ImportError:
        missing_deps.append("PyGithub")
        print("  ❌ PyGithub not found")
    
    try:
        import git
        print("  ✅ GitPython installed")
    except ImportError:
        missing_deps.append("GitPython")
        print("  ❌ GitPython not found")
    
    try:
        import mcp
        print("  ✅ MCP framework installed")
    except ImportError:
        missing_deps.append("mcp")
        print("  ❌ MCP framework not found")
    
    try:
        import aiohttp
        print("  ✅ aiohttp installed")
    except ImportError:
        missing_deps.append("aiohttp")
        print("  ❌ aiohttp not found")
    
    try:
        import pydantic
        print("  ✅ pydantic installed")
    except ImportError:
        missing_deps.append("pydantic")
        print("  ❌ pydantic not found")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with:")
        print("  uv sync  (recommended)")
        print("  or: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True

def test_github_token():
    """Test GitHub token configuration"""
    print("\n🔍 Checking GitHub token...")
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("  ❌ GITHUB_TOKEN environment variable not set")
        print("  Set it with: export GITHUB_TOKEN=your_token_here")
        return False
    
    print("  ✅ GITHUB_TOKEN environment variable found")
    
    # Test token validity
    try:
        from github import Github
        client = Github(token)
        user = client.get_user()
        print(f"  ✅ Token valid - Connected as: {user.login}")
        
        # Check token scopes
        rate_limit = client.get_rate_limit()
        print(f"  ✅ API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
        
        return True
    except Exception as e:
        print(f"  ❌ Token invalid or network error: {str(e)}")
        return False

def test_server_import():
    """Test if the server can be imported"""
    print("\n🔍 Testing server import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        from github_server import GitHubMCPServer
        print("  ✅ Server module imported successfully")
        
        # Try to create server instance
        server = GitHubMCPServer()
        print("  ✅ Server instance created successfully")
        
        return True
    except Exception as e:
        print(f"  ❌ Error importing server: {str(e)}")
        return False

def test_basic_functionality():
    """Test basic GitHub API functionality"""
    print("\n🔍 Testing basic GitHub functionality...")
    
    try:
        from github import Github
        token = os.getenv("GITHUB_TOKEN")
        client = Github(token)
        
        # Test listing repositories
        user = client.get_user()
        repos = list(user.get_repos(type="all"))[:5]  # Get first 5 repos
        
        print(f"  ✅ Successfully retrieved {len(repos)} repositories")
        
        if repos:
            repo = repos[0]
            print(f"  ✅ Sample repository: {repo.full_name}")
            
            # Test getting repository contents
            try:
                contents = repo.get_contents("")
                print(f"  ✅ Successfully accessed repository contents ({len(contents)} items)")
            except Exception as e:
                print(f"  ⚠️  Could not access repository contents: {str(e)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error testing GitHub functionality: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 GitHub MCP Connector - Setup Test\n")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("GitHub Token", test_github_token),
        ("Server Import", test_server_import),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ Unexpected error in {test_name}: {str(e)}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your GitHub MCP Connector is ready to use!")
        print("\nNext steps:")
        print("1. Add the server to your MCP client configuration")
        print("2. Start using it with commands like 'List my GitHub repositories'")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before using the connector.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
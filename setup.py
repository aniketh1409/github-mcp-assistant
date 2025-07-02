#!/usr/bin/env python3
"""
Setup script for GitHub MCP Connector
Helps users configure the connector securely
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up environment files and configuration"""
    print("🚀 GitHub MCP Connector Setup")
    print("=" * 40)
    
    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
    else:
        # Copy example env file
        example_env = Path("env.example")
        if example_env.exists():
            shutil.copy(example_env, env_file)
            print("✅ Created .env file from template")
            print("⚠️  IMPORTANT: Edit .env file and add your GitHub token!")
        else:
            print("❌ env.example file not found")
            return False
    
    # Get current directory
    current_dir = Path.cwd().absolute()
    server_path = current_dir / "github_server.py"
    
    print(f"\n📁 Project location: {current_dir}")
    print(f"🐍 Server script: {server_path}")
    
    # Show next steps
    print("\n🔑 Next Steps:")
    print("1. Get a GitHub Personal Access Token:")
    print("   → Go to: https://github.com/settings/tokens")
    print("   → Create token with scopes: repo, public_repo, user")
    print("   → Copy the token")
    
    print("\n2. Add your token to .env file:")
    print(f"   → Edit: {env_file.absolute()}")
    print("   → Set: GITHUB_TOKEN=your_actual_token_here")
    
    print("\n3. Test your setup:")
    print("   → Run: python test_setup.py")
    
    print("\n4. Configure your MCP client:")
    print("   → Use example files in this directory")
    print(f"   → Update server path to: {server_path}")
    
    print("\n🔒 Security Reminders:")
    print("   → Never commit your .env file")
    print("   → Never share your GitHub token")
    print("   → Use example files for sharing configurations")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    missing = []
    
    try:
        import github
        print("  ✅ PyGithub")
    except ImportError:
        missing.append("PyGithub")
        print("  ❌ PyGithub")
    
    try:
        import git
        print("  ✅ GitPython")
    except ImportError:
        missing.append("GitPython")
        print("  ❌ GitPython")
    
    try:
        import mcp
        print("  ✅ MCP")
    except ImportError:
        missing.append("mcp")
        print("  ❌ MCP")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install with:")
        print("  uv sync")
        print("  or: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True

def main():
    """Main setup function"""
    print("Setting up GitHub MCP Connector...\n")
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Setup environment
    env_ok = setup_environment()
    
    if deps_ok and env_ok:
        print("\n🎉 Setup complete!")
        print("Ready to run: python test_setup.py")
    else:
        print("\n⚠️  Setup incomplete. Please fix the issues above.")

if __name__ == "__main__":
    main() 
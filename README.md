# GitHub MCP Connector

A Model Context Protocol (MCP) server that provides GitHub repository management and file access capabilities to AI assistants.

## Features ✨

### Core Repository Management
- **List Repositories**: Browse all your GitHub repositories with filtering and sorting
- **Repository Information**: Get detailed information about any repository
- **File Browsing**: Navigate repository file structures remotely
- **File Reading**: Read file contents from any repository
- **Code Search**: Search for code content across repositories
- **File Search**: Find files by name or path

### Local Development Workflow
- **Clone Repositories**: Clone GitHub repos to your local filesystem
- **Local Repository Management**: List and manage locally cloned repositories
- **Smart Organization**: Automatically organize cloned repos in `~/github/{owner}/{repo}` structure

## Installation 🚀

### 0. Prerequisites
- **Python 3.10+** is required (MCP framework requirement)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/github-mcp-connector.git
cd github-mcp-connector

# Run the setup script
python setup.py
```

### 2. Install Dependencies

**Option A: Using uv (Recommended - Much Faster!)**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

**Option B: Using pip**
```bash
pip install -r requirements.txt
```

### 2. Get GitHub Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (Full control of private repositories)
   - `public_repo` (Access public repositories)
   - `user` (Read user profile data)

### 3. Set Up Environment Variables

**Option A: Using .env file (Recommended)**
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your actual GitHub token
# GITHUB_TOKEN=your_actual_token_here
```

**Option B: Set environment variable directly**
```bash
# On Windows PowerShell
$env:GITHUB_TOKEN="your_token_here"

# On Windows CMD
set GITHUB_TOKEN=your_token_here

# On macOS/Linux
export GITHUB_TOKEN=your_token_here
```

### 4. Register with MCP Client

**Copy and customize the example configuration:**
```bash
# For Claude Desktop
cp claude_desktop_config.example.json ~/.config/claude/claude_desktop_config.json

# For other MCP clients  
cp mcp_server_config.example.json your_mcp_config.json
```

**Or add manually to your MCP client configuration:**
```json
{
  "mcpServers": {
    "github-connector": {
      "command": "python",
      "args": ["/absolute/path/to/your/github_server.py"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**⚠️ Important:** 
- Replace `/absolute/path/to/your/github_server.py` with the actual path
- Ensure your `GITHUB_TOKEN` environment variable is set
- Never commit files containing your actual token

## Usage Examples 📖

### Repository Management

**List your repositories:**
```
Can you show me my GitHub repositories?
```

**Get repository details:**
```
Get information about my repository "my-awesome-project"
```

**Browse repository structure:**
```
Show me the file structure of microsoft/vscode
```

### File Operations

**Read a file:**
```
Read the README.md file from facebook/react
```

**Search for files:**
```
Find all Python files containing "main" in the django/django repository
```

**Search code content:**
```
Search for "async function" in microsoft/typescript
```

### Local Development

**Clone a repository:**
```
Clone the repository microsoft/vscode to my local machine
```

**List local repositories:**
```
Show me all the GitHub repositories I have cloned locally
```

## Available Tools 🛠️

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_repositories` | List user's GitHub repositories | `repo_type`, `sort`, `limit` |
| `get_repository_info` | Get detailed repository information | `repo_name` |
| `browse_repository` | Browse repository file structure | `repo_name`, `path`, `ref` |
| `read_file` | Read file contents from repository | `repo_name`, `file_path`, `ref` |
| `search_files` | Search for files by name/path | `repo_name`, `query`, `file_type` |
| `search_code` | Search code content within repository | `repo_name`, `query`, `language` |
| `clone_repository` | Clone repository to local filesystem | `repo_name`, `local_path`, `branch` |
| `list_local_repositories` | List locally cloned repositories | `base_path` |

## Configuration Options ⚙️

### Repository Types
- `all`: All repositories (default)
- `public`: Public repositories only
- `private`: Private repositories only
- `owner`: Repositories you own

### Sort Options
- `updated`: Recently updated (default)
- `created`: Recently created
- `pushed`: Recently pushed
- `full_name`: Alphabetical

## Error Handling 🔧

The server handles common scenarios:
- **Rate Limiting**: Respects GitHub API rate limits
- **Authentication**: Clear error messages for token issues
- **File Access**: Handles binary files and large files appropriately
- **Network Issues**: Graceful handling of connection problems

## Development 

### Project Structure
```
├── github_server.py                    # Main MCP server implementation
├── requirements.txt                    # Python dependencies (pip)
├── pyproject.toml                      # Project configuration (uv/modern Python)
├── setup.py                           # Setup script for easy configuration
├── test_setup.py                      # Setup verification script
├── env.example                        # Example environment variables
├── mcp_server_config.example.json     # Example MCP configuration
├── claude_desktop_config.example.json # Example Claude Desktop configuration
├── .gitignore                         # Git ignore patterns (protects secrets)
└── README.md                          # This file
```

### Dependencies
- `mcp>=1.0.0`: Model Context Protocol framework
- `PyGithub>=2.1.1`: GitHub API client
- `GitPython>=3.1.40`: Git operations for local repositories
- `aiohttp>=3.9.0`: Async HTTP client
- `pydantic>=2.0.0`: Data validation

### Running the Server

**With uv (recommended):**
```bash
# Run directly
uv run python github_server.py

# Or activate virtual environment first
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
python github_server.py
```

**With pip:**
```bash
python github_server.py
```

### Development with uv
```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check .
```

## Security Notes 🔐

### **Environment Variables & Secrets**
- ✅ **Use .env files**: Store sensitive data in `.env` (automatically ignored by git)
- ✅ **Example files**: Share configurations using `.example` files
- ❌ **Never commit tokens**: Real tokens should never be in version control
- ❌ **Never hardcode secrets**: Use environment variables or config files

### **GitHub Token Security**
- **Minimum Scopes**: Only grant `repo`, `public_repo`, and `user` scopes
- **Token Rotation**: Regularly regenerate your personal access tokens
- **Secure Storage**: Store tokens in environment variables, not code files
- **Access Control**: Tokens inherit your GitHub permissions

### **Server Security**
- **Local Only**: Server runs locally, never exposes tokens to external services
- **Rate Limiting**: Automatically respects GitHub's API rate limits
- **Error Handling**: Provides detailed error messages without exposing sensitive data
- **Permissions**: Only accesses repositories you have permission to view

### **Development Best Practices**
- Always use the `setup.py` script for initial configuration
- Test with `test_setup.py` before using in production
- Keep dependencies updated with `uv sync` or `pip install -U`
- Use example configurations as templates, never share real configs

## Limitations 

- **Search Rate Limits**: GitHub code search has stricter rate limits
- **Large Files**: Files over 1MB may be truncated
- **Binary Files**: Binary files are not displayed (but can be detected)
- **Private Repositories**: Requires appropriate token permissions

## Future Enhancements 

Planned features for future versions:
- Issue management (create, update, comment)
- Pull request operations (create, review, merge)
- Branch management (create, switch, delete)
- Commit operations (commit, push changes)
- Webhook management
- GitHub Actions integration

## Contributing 

Feel free to submit issues and enhancement requests!

## License 

Feel free to use this in your own projects.

Made by Aniketh Kini
---

**Ready to connect your AI assistant to GitHub!** 🎉 
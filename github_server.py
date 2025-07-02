#!/usr/bin/env python3
"""
GitHub MCP Server - Connect to GitHub repositories and manage files
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from github import Github, Repository
from git import Repo, InvalidGitRepositoryError
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types


class GitHubMCPServer:
    def __init__(self):
        self.github_client = None
        self.server = Server("github-connector")
        self.setup_tools()
        
    def setup_tools(self):
        """Register all available tools"""
        
        # Repository Management Tools
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="list_repositories",
                    description="List user's GitHub repositories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_type": {
                                "type": "string",
                                "enum": ["all", "public", "private", "owner"],
                                "default": "all",
                                "description": "Type of repositories to list"
                            },
                            "sort": {
                                "type": "string",
                                "enum": ["created", "updated", "pushed", "full_name"],
                                "default": "updated",
                                "description": "Sort repositories by"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 30,
                                "description": "Maximum number of repositories to return"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_repository_info",
                    description="Get detailed information about a specific repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo' or just 'repo' for user's repos"
                            }
                        },
                        "required": ["repo_name"]
                    }
                ),
                types.Tool(
                    name="browse_repository",
                    description="Browse repository file structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "path": {
                                "type": "string",
                                "default": "",
                                "description": "Path within repository (optional, defaults to root)"
                            },
                            "ref": {
                                "type": "string",
                                "description": "Branch or commit reference (optional, defaults to main branch)"
                            }
                        },
                        "required": ["repo_name"]
                    }
                ),
                types.Tool(
                    name="read_file",
                    description="Read file contents from a GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file within the repository"
                            },
                            "ref": {
                                "type": "string",
                                "description": "Branch or commit reference (optional, defaults to main branch)"
                            }
                        },
                        "required": ["repo_name", "file_path"]
                    }
                ),
                types.Tool(
                    name="search_files",
                    description="Search for files by name or path in a repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query for file names or paths"
                            },
                            "file_type": {
                                "type": "string",
                                "description": "File extension to filter by (optional)"
                            }
                        },
                        "required": ["repo_name", "query"]
                    }
                ),
                types.Tool(
                    name="search_code",
                    description="Search code content within a repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "query": {
                                "type": "string",
                                "description": "Code search query"
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language to filter by (optional)"
                            }
                        },
                        "required": ["repo_name", "query"]
                    }
                ),
                types.Tool(
                    name="clone_repository",
                    description="Clone a GitHub repository to local filesystem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "local_path": {
                                "type": "string",
                                "description": "Local path where to clone the repository (optional)"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Specific branch to clone (optional)"
                            }
                        },
                        "required": ["repo_name"]
                    }
                ),
                types.Tool(
                    name="list_local_repositories",
                    description="List locally cloned repositories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_path": {
                                "type": "string",
                                "description": "Base path to search for repositories (optional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="create_repository",
                    description="Create a new GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Repository name"
                            },
                            "description": {
                                "type": "string",
                                "description": "Repository description (optional)"
                            },
                            "private": {
                                "type": "boolean",
                                "default": False,
                                "description": "Whether the repository should be private"
                            },
                            "init_readme": {
                                "type": "boolean",
                                "default": True,
                                "description": "Initialize repository with README"
                            },
                            "gitignore_template": {
                                "type": "string",
                                "description": "Gitignore template (e.g., 'Python', 'Node', 'Java')"
                            },
                            "license_template": {
                                "type": "string",
                                "description": "License template (e.g., 'mit', 'apache-2.0', 'gpl-3.0')"
                            }
                        },
                        "required": ["name"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            try:
                if not self.github_client:
                    return [types.TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please set GITHUB_TOKEN environment variable."
                    )]
                
                if name == "list_repositories":
                    return await self._list_repositories(**arguments)
                elif name == "get_repository_info":
                    return await self._get_repository_info(**arguments)
                elif name == "browse_repository":
                    return await self._browse_repository(**arguments)
                elif name == "read_file":
                    return await self._read_file(**arguments)
                elif name == "search_files":
                    return await self._search_files(**arguments)
                elif name == "search_code":
                    return await self._search_code(**arguments)
                elif name == "clone_repository":
                    return await self._clone_repository(**arguments)
                elif name == "list_local_repositories":
                    return await self._list_local_repositories(**arguments)
                elif name == "create_repository":
                    return await self._create_repository(**arguments)
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    async def _list_repositories(self, repo_type: str = "all", sort: str = "updated", limit: int = 30) -> list[types.TextContent]:
        """List user's repositories"""
        try:
            user = self.github_client.get_user()
            
            if repo_type == "all":
                repos = user.get_repos(sort=sort)
            elif repo_type == "public":
                repos = user.get_repos(type="public", sort=sort)
            elif repo_type == "private":
                repos = user.get_repos(type="private", sort=sort)
            elif repo_type == "owner":
                repos = user.get_repos(type="owner", sort=sort)
            
            repo_list = []
            count = 0
            for repo in repos:
                if count >= limit:
                    break
                repo_list.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "updated": repo.updated_at.isoformat(),
                    "url": repo.html_url
                })
                count += 1
            
            return [types.TextContent(
                type="text",
                text=f"Found {len(repo_list)} repositories:\n\n" + 
                     "\n".join([f"• **{repo['full_name']}** ({repo['language'] or 'Unknown'})\n"
                               f"  {repo['description'] or 'No description'}\n"
                               f"  Stars: {repo['stars']} | Forks: {repo['forks']} | Updated: {repo['updated'][:10]}\n"
                               for repo in repo_list])
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error listing repositories: {str(e)}"
            )]

    async def _get_repository_info(self, repo_name: str) -> list[types.TextContent]:
        """Get detailed repository information"""
        try:
            repo = self.github_client.get_repo(repo_name)
            
            info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "size": repo.size,
                "default_branch": repo.default_branch,
                "created": repo.created_at.isoformat(),
                "updated": repo.updated_at.isoformat(),
                "pushed": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "homepage": repo.homepage,
                "license": repo.license.name if repo.license else None,
                "topics": repo.get_topics(),
                "open_issues": repo.open_issues_count,
            }
            
            info_text = f"""# {info['full_name']}

**Description:** {info['description'] or 'No description'}

## Repository Details
- **Language:** {info['language'] or 'Not specified'}
- **Private:** {'Yes' if info['private'] else 'No'}
- **Default Branch:** {info['default_branch']}
- **Size:** {info['size']} KB
- **License:** {info['license'] or 'Not specified'}

## Statistics
- **Stars:** {info['stars']}
- **Forks:** {info['forks']}
- **Watchers:** {info['watchers']}
- **Open Issues:** {info['open_issues']}

## Dates
- **Created:** {info['created'][:10]}
- **Updated:** {info['updated'][:10]}
- **Last Push:** {info['pushed'][:10] if info['pushed'] else 'Never'}

## URLs
- **Repository:** {repo.html_url}
- **Clone (HTTPS):** {info['clone_url']}
- **Clone (SSH):** {info['ssh_url']}
{f"- **Homepage:** {info['homepage']}" if info['homepage'] else ""}

## Topics
{', '.join(info['topics']) if info['topics'] else 'No topics'}
"""
            
            return [types.TextContent(type="text", text=info_text)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting repository info: {str(e)}"
            )]

    async def _browse_repository(self, repo_name: str, path: str = "", ref: str = None) -> list[types.TextContent]:
        """Browse repository file structure"""
        try:
            repo = self.github_client.get_repo(repo_name)
            
            # Get contents at the specified path
            try:
                contents = repo.get_contents(path, ref=ref)
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error accessing path '{path}': {str(e)}"
                )]
            
            # Handle single file vs directory
            if not isinstance(contents, list):
                contents = [contents]
            
            # Sort: directories first, then files
            dirs = [item for item in contents if item.type == "dir"]
            files = [item for item in contents if item.type == "file"]
            
            result = f"# {repo_name}{':' + path if path else ''}\n\n"
            
            if dirs:
                result += "## Directories\n"
                for item in sorted(dirs, key=lambda x: x.name.lower()):
                    result += f"**{item.name}/**\n"
                result += "\n"
            
            if files:
                result += "## Files\n"
                for item in sorted(files, key=lambda x: x.name.lower()):
                    size_kb = item.size / 1024 if item.size else 0
                    result += f"**{item.name}** ({size_kb:.1f} KB)\n"
            
            if not dirs and not files:
                result += "*Empty directory*\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error browsing repository: {str(e)}"
            )]

    async def _read_file(self, repo_name: str, file_path: str, ref: str = None) -> list[types.TextContent]:
        """Read file contents from repository"""
        try:
            repo = self.github_client.get_repo(repo_name)
            file_content = repo.get_contents(file_path, ref=ref)
            
            if file_content.type != "file":
                return [types.TextContent(
                    type="text",
                    text=f"Error: '{file_path}' is not a file"
                )]
            
            # Decode content
            content = file_content.decoded_content.decode('utf-8')
            
            # Get file info
            size_kb = file_content.size / 1024
            
            result = f"""# {file_path}

**Repository:** {repo_name}
**Size:** {size_kb:.1f} KB
**Last Modified:** {file_content.last_modified or 'Unknown'}

## Content

```
{content}
```
"""
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error reading file: {str(e)}"
            )]

    async def _search_files(self, repo_name: str, query: str, file_type: str = None) -> list[types.TextContent]:
        """Search for files by name or path"""
        try:
            # Build search query
            search_query = f"repo:{repo_name} filename:{query}"
            if file_type:
                search_query += f" extension:{file_type}"
            
            # Search using GitHub API
            results = self.github_client.search_code(search_query)
            
            files = []
            for item in results:
                files.append({
                    "name": item.name,
                    "path": item.path,
                    "url": item.html_url,
                    "repository": item.repository.full_name
                })
            
            if not files:
                return [types.TextContent(
                    type="text",
                    text=f"No files found matching '{query}' in {repo_name}"
                )]
            
            result = f"# File Search Results\n\n**Query:** {query}\n**Repository:** {repo_name}\n\n"
            
            for file in files[:20]:  # Limit to 20 results
                result += f"**{file['name']}**\n"
                result += f"   Path: `{file['path']}`\n"
                result += f"   [View on GitHub]({file['url']})\n\n"
            
            if len(files) > 20:
                result += f"*... and {len(files) - 20} more results*\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error searching files: {str(e)}"
            )]

    async def _search_code(self, repo_name: str, query: str, language: str = None) -> list[types.TextContent]:
        """Search code content within repository"""
        try:
            # Build search query
            search_query = f"repo:{repo_name} {query}"
            if language:
                search_query += f" language:{language}"
            
            # Search using GitHub API
            results = self.github_client.search_code(search_query)
            
            matches = []
            for item in results:
                matches.append({
                    "file": item.name,
                    "path": item.path,
                    "url": item.html_url,
                    "repository": item.repository.full_name
                })
            
            if not matches:
                return [types.TextContent(
                    type="text",
                    text=f"No code matches found for '{query}' in {repo_name}"
                )]
            
            result = f"# Code Search Results\n\n**Query:** {query}\n**Repository:** {repo_name}\n\n"
            
            for match in matches[:15]:  # Limit to 15 results
                result += f"**{match['file']}**\n"
                result += f"   Path: `{match['path']}`\n"
                result += f"   [View on GitHub]({match['url']})\n\n"
            
            if len(matches) > 15:
                result += f"*... and {len(matches) - 15} more results*\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error searching code: {str(e)}"
            )]

    async def _clone_repository(self, repo_name: str, local_path: str = None, branch: str = None) -> list[types.TextContent]:
        """Clone repository to local filesystem"""
        try:
            repo = self.github_client.get_repo(repo_name)
            
            # Determine local path
            if not local_path:
                # Default to ~/github/{owner}/{repo}
                home = Path.home()
                owner, repo_name_only = repo_name.split('/')
                local_path = home / "github" / owner / repo_name_only
            else:
                local_path = Path(local_path)
            
            # Create parent directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if directory already exists
            if local_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Error: Directory '{local_path}' already exists. Choose a different path or remove the existing directory."
                )]
            
            # Clone the repository
            clone_url = repo.clone_url
            
            if branch:
                cloned_repo = Repo.clone_from(clone_url, local_path, branch=branch)
            else:
                cloned_repo = Repo.clone_from(clone_url, local_path)
            
            # Get some info about the cloned repo
            current_branch = cloned_repo.active_branch.name
            commit_count = len(list(cloned_repo.iter_commits()))
            
            result = f"""# Repository Cloned Successfully

**Repository:** {repo_name}
**Local Path:** {local_path}
**Branch:** {current_branch}
**Commits:** {commit_count}

The repository has been cloned to your local filesystem and is ready for development!
"""
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error cloning repository: {str(e)}"
            )]

    async def _list_local_repositories(self, base_path: str = None) -> list[types.TextContent]:
        """List locally cloned repositories"""
        try:
            if not base_path:
                # Default search paths
                search_paths = [
                    Path.home() / "github",
                    Path.home() / "projects", 
                    Path.home() / "code",
                    Path.cwd()
                ]
            else:
                search_paths = [Path(base_path)]
            
            local_repos = []
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                    
                # Look for git repositories
                for item in search_path.rglob('.git'):
                    if item.is_dir():
                        repo_path = item.parent
                        try:
                            git_repo = Repo(repo_path)
                            
                            # Get remote info
                            remote_url = None
                            if git_repo.remotes:
                                remote_url = git_repo.remotes.origin.url
                            
                            # Get current branch
                            current_branch = git_repo.active_branch.name if git_repo.active_branch else "detached"
                            
                            # Check if there are uncommitted changes
                            is_dirty = git_repo.is_dirty()
                            
                            local_repos.append({
                                "path": str(repo_path),
                                "name": repo_path.name,
                                "remote_url": remote_url,
                                "current_branch": current_branch,
                                "is_dirty": is_dirty,
                                "last_commit": git_repo.head.commit.hexsha[:8] if git_repo.head.commit else None
                            })
                        except InvalidGitRepositoryError:
                            continue
            
            if not local_repos:
                return [types.TextContent(
                    type="text",
                    text="No local Git repositories found in the searched paths."
                )]
            
            result = f"# Local Git Repositories\n\n**Found {len(local_repos)} repositories:**\n\n"
            
            for repo in local_repos:
                status = "dirty" if repo['is_dirty'] else "clean"
                result += f"## {repo['name']}\n"
                result += f"**Path:** `{repo['path']}`\n"
                result += f"**Branch:** {repo['current_branch']} | **Status:** {status}\n"
                if repo['remote_url']:
                    result += f"**Remote:** {repo['remote_url']}\n"
                if repo['last_commit']:
                    result += f"**Last Commit:** {repo['last_commit']}\n"
                result += "\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error listing local repositories: {str(e)}"
            )]

    async def _create_repository(self, name: str, description: str = None, private: bool = False, 
                               init_readme: bool = True, gitignore_template: str = None, 
                               license_template: str = None) -> list[types.TextContent]:
        """Create a new GitHub repository"""
        try:
            user = self.github_client.get_user()
            
            # Validate repository name
            if not name or not name.strip():
                return [types.TextContent(
                    type="text",
                    text="Error: Repository name cannot be empty"
                )]
            
            # Clean up parameters - GitHub API doesn't accept None values for templates
            create_params = {
                "name": name.strip(),
                "private": private,
                "auto_init": init_readme
            }
            
            if description and description.strip():
                create_params["description"] = description.strip()
            
            if gitignore_template and gitignore_template.strip():
                create_params["gitignore_template"] = gitignore_template.strip()
            
            if license_template and license_template.strip():
                create_params["license_template"] = license_template.strip()
            
            # Create repository
            repo = user.create_repo(**create_params)
            
            result = f"""# Repository Created Successfully!

**Repository:** {repo.full_name}
**Description:** {repo.description or 'No description'}
**Visibility:** {'Private' if repo.private else 'Public'}
**Default Branch:** {repo.default_branch}

## Repository Details
- **Created:** {repo.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Clone URL (HTTPS):** {repo.clone_url}
- **Clone URL (SSH):** {repo.ssh_url}
- **Repository URL:** {repo.html_url}

## Quick Start
```bash
# Clone your new repository
git clone {repo.clone_url}
cd {name}

# Start developing!
```

Your new repository is ready for development!
"""
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            error_msg = f"Error creating repository: {type(e).__name__}: {str(e)}"
            
            # Handle common GitHub API errors
            if hasattr(e, 'status') and hasattr(e, 'data'):
                if e.status == 422:
                    error_msg = f"Repository creation failed: Repository '{name}' already exists or invalid parameters"
                elif e.status == 403:
                    error_msg = "Repository creation failed: Insufficient permissions or rate limit exceeded"
                elif e.status == 401:
                    error_msg = "Repository creation failed: Authentication failed - check your GitHub token"
                else:
                    error_msg = f"GitHub API Error {e.status}: {e.data.get('message', str(e))}"
            
            return [types.TextContent(
                type="text",
                text=error_msg
            )]

    def init_github_client(self):
        """Initialize GitHub client with token"""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.github_client = Github(token)
        
        # Test the connection
        try:
            user = self.github_client.get_user()
            # Don't print to stdout - it interferes with MCP protocol
            # Connection successful if we get here
        except Exception as e:
            raise ValueError(f"Failed to connect to GitHub: {e}")

    async def run(self):
        """Run the MCP server"""
        # Initialize GitHub client
        try:
            self.init_github_client()
        except ValueError as e:
            # Don't print to stdout - it interferes with MCP protocol
            # Log error internally or exit silently
            return
        
        # Import and run the server
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="github-connector",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


if __name__ == "__main__":
    server = GitHubMCPServer()
    asyncio.run(server.run()) 
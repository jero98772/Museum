import requests
import subprocess
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Repository:
    """Data class to store repository information"""
    title: str
    url: str
    description: Optional[str]
    
    def __repr__(self):
        return f"Repository(title='{self.title}', url='{self.url}', description='{self.description}')"


class GitHubRepoFetcher:
    """
    Fetches GitHub repository information for a given username.
    Tries using requests first, falls back to gh CLI if that fails.
    """
    
    def __init__(self, username: str):
        self.username = username
        self.api_url = f"https://api.github.com/users/{username}/repos"
    
    def fetch_repos(self) -> List[Repository]:
        """
        Fetch all repositories for the username.
        Returns a list of Repository objects.
        """
        try:
            return self._fetch_with_requests()
        except Exception as e:
            print(f"Failed to fetch with requests: {e}")
            print("Attempting to use gh CLI...")
            return self._fetch_with_gh_cli()
    
    def _fetch_with_requests(self) -> List[Repository]:
        """Fetch repositories using requests library"""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            response = requests.get(
                self.api_url,
                params={'page': page, 'per_page': per_page},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                break
            
            for repo in data:
                repos.append(Repository(
                    title=repo['name'],
                    url=repo['html_url'],
                    description=repo['description']
                ))
            
            page += 1
            
            # Check if there are more pages
            if len(data) < per_page:
                break
        
        return repos
    
    def _fetch_with_gh_cli(self) -> List[Repository]:
        """Fetch repositories using gh CLI"""
        try:
            # Check if gh CLI is installed
            subprocess.run(['gh', '--version'], 
                         capture_output=True, 
                         check=True)
            
            # Fetch repos using gh CLI
            result = subprocess.run(
                ['gh', 'repo', 'list', self.username, '--json', 
                 'name,url,description', '--limit', '1000'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            repos = []
            
            for repo in data:
                repos.append(Repository(
                    title=repo['name'],
                    url=repo['url'],
                    description=repo.get('description')
                ))
            
            return repos
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"gh CLI command failed: {e.stderr}")
        except FileNotFoundError:
            raise Exception("gh CLI is not installed. Please install it from https://cli.github.com/")
    
    def print_repos(self):
        """Fetch and print all repositories"""
        repos = self.fetch_repos()
        
        if not repos:
            print(f"No repositories found for user: {self.username}")
            return
        
        print(f"\nFound {len(repos)} repositories for {self.username}:\n")
        
        for i, repo in enumerate(repos, 1):
            print(f"{i}. {repo.title}")
            print(f"   URL: {repo.url}")
            print(f"   Description: {repo.description or 'No description'}")
            print()


# Example usage
if __name__ == "__main__":
    # Replace with any GitHub username
    username = "torvalds"
    
    fetcher = GitHubRepoFetcher(username)
    fetcher.print_repos()
    
    # Or get the repos as a list
    # repos = fetcher.fetch_repos()
    # for repo in repos:
    #     print(repo)

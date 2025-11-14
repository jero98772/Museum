import requests
import subprocess
import json
import base64
import os
from typing import List, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

@dataclass
class Repository:
    """Data class to store repository information"""
    title: str
    url: str
    description: Optional[str]
    readme: Optional[str] = None
    
    def __repr__(self):
        return f"Repository(title='{self.title}', url='{self.url}', readme_length={len(self.readme) if self.readme else 0})"
    
    def to_dict(self):
        """Convert Repository to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Repository from dictionary"""
        return cls(**data)

class GitHubRepoFetcher:
    """
    Fetches GitHub repository information for a given username.
    Supports caching to file and parallel README fetching.
    """
    
    def __init__(self, username: str, cache_file: Optional[str] = None, max_workers: int = 10):
        self.username = username
        self.api_url = f"https://api.github.com/users/{username}/repos"
        self.cache_file = cache_file or f"data/{username}_repos.json"
        self.max_workers = max_workers
        self.print_lock = Lock()
    
    def fetch_repos(self, force_refresh: bool = False) -> List[Repository]:
        """
        Fetch all repositories for the username.
        Checks cache first unless force_refresh is True.
        Returns a list of Repository objects.
        """
        # Check if cache exists and we're not forcing refresh
        if not force_refresh and os.path.exists(self.cache_file):
            print(f"Loading repositories from cache: {self.cache_file}")
            return self._load_from_cache()
        
        # Fetch fresh data
        print(f"Fetching repositories for {self.username}...")
        try:
            repos = self._fetch_with_requests()
        except Exception as e:
            print(f"Failed to fetch with requests: {e}")
            print("Attempting to use gh CLI...")
            repos = self._fetch_with_gh_cli()
        
        # Save to cache
        self._save_to_cache(repos)
        
        return repos
    
    def _load_from_cache(self) -> List[Repository]:
        """Load repositories from cache file"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Repository.from_dict(repo) for repo in data]
        except Exception as e:
            raise Exception(f"Failed to load from cache: {e}")
    
    def _save_to_cache(self, repos: List[Repository]):
        """Save repositories to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump([repo.to_dict() for repo in repos], f, indent=2, ensure_ascii=False)
            print(f"Saved {len(repos)} repositories to {self.cache_file}")
        except Exception as e:
            print(f"Failed to save to cache: {e}")
    
    def _safe_print(self, message: str):
        """Thread-safe printing"""
        with self.print_lock:
            print(message)
    
    def _fetch_readme(self, repo_name: str) -> Optional[str]:
        """Fetch README content for a repository using requests"""
        readme_url = f"https://api.github.com/repos/{self.username}/{repo_name}/readme"
        
        try:
            response = requests.get(readme_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            else:
                return None
        except Exception as e:
            self._safe_print(f"Failed to fetch README for {repo_name}: {e}")
            return None
    
    def _fetch_repo_with_readme(self, repo_data: dict) -> Repository:
        """Fetch a single repository with its README"""
        repo_name = repo_data['name']
        self._safe_print(f"Fetching README for {repo_name}...")
        
        readme = self._fetch_readme(repo_name)
        
        return Repository(
            title=repo_name,
            url=repo_data['html_url'],
            description=repo_data['description'],
            readme=readme
        )
    
    def _fetch_with_requests(self) -> List[Repository]:
        """Fetch repositories using requests library with parallel README fetching"""
        # First, get all repository metadata
        all_repos_data = []
        page = 1
        per_page = 100
        
        print("Fetching repository list...")
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
            
            all_repos_data.extend(data)
            page += 1
            
            if len(data) < per_page:
                break
        
        print(f"Found {len(all_repos_data)} repositories. Fetching READMEs in parallel...")
        
        # Fetch READMEs in parallel
        repos = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_repo = {
                executor.submit(self._fetch_repo_with_readme, repo_data): repo_data
                for repo_data in all_repos_data
            }
            
            for future in as_completed(future_to_repo):
                try:
                    repo = future.result()
                    repos.append(repo)
                except Exception as e:
                    repo_data = future_to_repo[future]
                    self._safe_print(f"Error processing {repo_data['name']}: {e}")
        
        return repos
    
    def _fetch_readme_with_gh_cli(self, repo_name: str) -> Optional[str]:
        """Fetch README content using gh CLI"""
        # Try different README filename variations
        readme_variations = [
            'README.md', 'readme.md', 'Readme.md',
            'README.MD', 'readme.MD', 'Readme.MD',
            'README', 'readme', 'Readme',
            'README.txt', 'readme.txt', 'Readme.txt',
            'README.rst', 'readme.rst', 'Readme.rst'
        ]
        
        for readme_name in readme_variations:
            try:
                result = subprocess.run(
                    ['gh', 'api', f'/repos/{self.username}/{repo_name}/contents/{readme_name}'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                data = json.loads(result.stdout)
                if 'content' in data:
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
            except subprocess.CalledProcessError:
                continue
            except Exception as e:
                self._safe_print(f"Error decoding README for {repo_name}: {e}")
                continue
        
        return None
    
    def _fetch_repo_with_readme_gh_cli(self, repo_data: dict) -> Repository:
        """Fetch a single repository with its README using gh CLI"""
        repo_name = repo_data['name']
        self._safe_print(f"Fetching README for {repo_name}...")
        
        readme = self._fetch_readme_with_gh_cli(repo_name)
        
        return Repository(
            title=repo_name,
            url=repo_data['url'],
            description=repo_data.get('description'),
            readme=readme
        )
    
    def _fetch_with_gh_cli(self) -> List[Repository]:
        """Fetch repositories using gh CLI with parallel README fetching"""
        try:
            # Check if gh CLI is installed
            subprocess.run(['gh', '--version'], 
                         capture_output=True, 
                         check=True)
            
            # Fetch repos using gh CLI
            print("Fetching repository list...")
            result = subprocess.run(
                ['gh', 'repo', 'list', self.username, '--json', 
                 'name,url,description', '--limit', '1000'],
                capture_output=True,
                text=True,
                check=True
            )
            
            all_repos_data = json.loads(result.stdout)
            print(f"Found {len(all_repos_data)} repositories. Fetching READMEs in parallel...")
            
            # Fetch READMEs in parallel
            repos = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_repo = {
                    executor.submit(self._fetch_repo_with_readme_gh_cli, repo_data): repo_data
                    for repo_data in all_repos_data
                }
                
                for future in as_completed(future_to_repo):
                    try:
                        repo = future.result()
                        repos.append(repo)
                    except Exception as e:
                        repo_data = future_to_repo[future]
                        self._safe_print(f"Error processing {repo_data['name']}: {e}")
            
            return repos
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"gh CLI command failed: {e.stderr}")
        except FileNotFoundError:
            raise Exception("gh CLI is not installed. Please install it from https://cli.github.com/")
    
    def print_repos(self, force_refresh: bool = False):
        """Fetch and print all repositories"""
        repos = self.fetch_repos(force_refresh=force_refresh)
        
        if not repos:
            print(f"No repositories found for user: {self.username}")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(repos)} repositories for {self.username}")
        print(f"{'='*80}\n")
        
        for i, repo in enumerate(repos, 1):
            print(f"{i}. {repo.title}")
            print(f"   URL: {repo.url}")
            print(f"   Description: {repo.description or 'No description'}")
            print(f"   README: {'✓ Available' if repo.readme else '✗ Not found'}")
            if repo.readme:
                print(f"   README length: {len(repo.readme)} characters")
            print()
    
    def get_repos_with_readme(self, force_refresh: bool = False) -> List[Repository]:
        """Get only repositories that have READMEs"""
        repos = self.fetch_repos(force_refresh=force_refresh)
        return [repo for repo in repos if repo.readme]

"""
# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch GitHub repositories with READMEs')
    parser.add_argument('username', help='GitHub username')
    parser.add_argument('--cache-file', '-f', help='Cache file name (default: {username}_repos.json)')
    parser.add_argument('--force-refresh', '-r', action='store_true', help='Force refresh from GitHub')
    parser.add_argument('--workers', '-w', type=int, default=10, help='Number of parallel workers (default: 10)')
    
    args = parser.parse_args()
    
    fetcher = GitHubRepoFetcher(
        username=args.username,
        cache_file=args.cache_file,
        max_workers=args.workers
    )
    
    fetcher.print_repos(force_refresh=args.force_refresh)
    
    # Get repos if needed
    repos = fetcher.fetch_repos()
    print(f"\nTotal repositories with READMEs: {len([r for r in repos if r.readme])}/{len(repos)}")
    print(len(repos))
"""
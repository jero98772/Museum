from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from tools.github import GitHubRepoFetcher
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Your GitHubRepoFetcher class should be imported here
# from your_module import GitHubRepoFetcher

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/map", response_class=HTMLResponse)
async def map_view(request: Request, username: str = Form(...)):
    fetcher = GitHubRepoFetcher(username)
    data = fetcher.fetch_repos()
    print(data)
    print(username)
    
    # Convert Repository objects to dictionaries for JSON serialization
    repos_data = [
        {
            "title": repo.title,
            "url": "https://github.com/jero98772",
            "description": "das"
        }
        for repo in data
    ]
    
    return templates.TemplateResponse("map.html", {
        "request": request,
        "username": username,
        "repos_data": repos_data  # Pass the data
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from tools.github import GitHubRepoFetcher
from tools.map_generator import generate_random_rooms ,initial_position

import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/map", response_class=HTMLResponse)
async def map_view(request: Request, username: str = Form(...)):
    fetcher = GitHubRepoFetcher(username)
    data = fetcher.fetch_repos()
    print(data)
    print(username)

    repos_amount = len(data)
    mid = repos_amount//2

    
    generate_map = generate_random_rooms(mid, mid,repos_amount)
    x,y = initial_position(generate_map)
    print(x,y)
    # Convert Repository objects to dictionaries for JSON serialization
    repos_data = [
        {
            "title": repo.title,
            "url":repo.url,
            "description": repo.description,
            "readme":repo.readme
        }
        for repo in data
    ]
    
    return templates.TemplateResponse("map.html", {
        "request": request,
        "username": username,
        "repos_data": repos_data,
        "map":generate_map,
        "x":x,
        "y":y,
        "map_size":mid,

    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
# 🎨 Museum

A 3D virtual museum where your GitHub repositories are displayed as interactive portals in a retro first-person dungeon crawler. Walk through procedurally generated corridors, discover golden doors representing your projects, and view their READMEs as curated art pieces.


## 🎮 Features

- **First-Person 3D Exploration**: Navigate through a Wolfenstein-style raycasted environment
- **Procedural Generation**: Each run creates a unique dungeon layout
- **Interactive Repository Portals**: Golden doors that open to display repository READMEs
- **Markdown Rendering**: Beautiful formatting of your project documentation
- **Minimap**: Real-time navigation aid showing your position and the map layout
- **Dual API Fetching**: Automatic fallback between GitHub API and CLI for reliability
- **Smart Caching**: Saves repository data to avoid rate limits

## 📸 Screenshots

<div align="center">
  <img src="" width="45%" alt="Dungeon exploration">
  <img src="" width="45%" alt="Repository README view">
</div>

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) GitHub CLI for enhanced API limits

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jero98772/museum.git
cd museum
```

2. **Install dependencies**
```bash
pip install fastapi uvicorn jinja2 python-multipart requests
```

3. **Run the server**
```bash
python main.py
```

4. **Open your browser**
```
http://localhost:9600
```

The server will automatically fetch your GitHub repositories and generate a unique museum for you to explore!

## 🎯 Usage

### Controls

| Key | Action |
|-----|--------|
| **W** / **↑** | Move forward |
| **S** / **↓** | Move backward |
| **A** / **←** | Turn left |
| **D** / **→** | Turn right |
| **E** | Interact with door (open repository README) |
| **ESC** | Close README overlay |

### Navigation Tips

- Look for **golden doors** 🟡 - these are your repository portals
- Use the **minimap** in the corner to navigate the dungeon
- When facing a door, press **E** to view the repository's README
- The **FPS counter** and **position** are displayed in the top-left

## ⚙️ Configuration

### Change GitHub Username

Edit `main.py` and modify the username:

```python
# Fetch repositories
fetcher = GitHubRepoFetcher('YOUR_GITHUB_USERNAME')
```

## 🔧 Advanced Setup

### Using GitHub CLI (Optional)

For higher API rate limits, install GitHub CLI:

```bash
# macOS
brew install gh

# Linux
sudo apt install gh

# Windows
winget install GitHub.cli
```

Then authenticate:
```bash
gh auth login
```

The application will automatically use the CLI if available, providing 5,000 requests/hour instead of 60.

### Running in Production

For production deployment, use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9600 main:app
```

## 🐛 Troubleshooting

### Issue: No repositories showing

**Solution**: Check the console for errors. Verify your GitHub username is correct and public repositories exist or install **GitHub CLI**.

### Issue: Rate limit exceeded

**Solution**: 
- Wait for the rate limit to reset (check GitHub's response headers)
- Install and authenticate with GitHub CLI
- Use cached data (stored in `data/` folder)

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

- 🎨 Add texture mapping to walls
- 🔦 Implement dynamic lighting system
- 👥 Multi-player support
- 🏆 Achievement system for exploring repositories
- 🔍 Search functionality to find specific repos
- 📱 Mobile touch controls
- 🎵 Background music and sound effects

## 📝 How It Works

This project combines three main technologies:

1. **Raycasting Engine**: A Wolfenstein 3D-style rendering technique that creates pseudo-3D graphics from a 2D map
2. **Procedural Generation**: Algorithms that create unique dungeon layouts every time
3. **GitHub API**: Fetches repository data and READMEs to populate the museum

For a detailed technical explanation, see [TECHNICAL.md](TECHNICAL.md).

## 📄 License

GLPv3 License - feel free to use this project for your own GitHub portfolio!

## 🌟 Inspiration

This project was inspired by:
- **Doom** - Classic raycasting game engine
- **Hackerspace Unloquer** - in a museom when the only fixed art work is a Hackerspace 
- **Open/free source** - make the code Free and Open for copy,paste distribute and modificate


---

<div align="center">
  <p>Built with ❤️ for developers who want to showcase their art in style</p>
  <p>⭐ Star this repo if you found it interesting!</p>
</div>
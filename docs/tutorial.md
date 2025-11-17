# Building a GitHub Repository Museum: A Technical Deep Dive

## Overview

This tutorial explains how to build a 3D virtual museum that displays GitHub repositories as interactive portals in a first-person dungeon crawler. Players explore a procedurally generated maze where each golden door represents a repository, and interacting with it displays the repository's README as an art piece.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Raycasting Rendering Engine](#raycasting-rendering-engine)
3. [Procedural Map Generation](#procedural-map-generation)
4. [GitHub API Integration](#github-api-integration)
5. [Dynamic Door-to-Repository Mapping](#dynamic-door-to-repository-mapping)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────┐
│  Backend (Python/Flask)                         │
│  ├─ GitHub API Fetcher                          │
│  ├─ Procedural Map Generator                    │
│  └─ Template Renderer                           │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  Frontend (JavaScript Canvas)                   │
│  ├─ Raycasting Engine                           │
│  ├─ Player Controller                           │
│  ├─ Door Interaction System                     │
│  └─ README Markdown Renderer                    │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. **Initialization**: Backend fetches GitHub repositories (with caching)
2. **Map Generation**: Procedural algorithm creates dungeon layout
3. **Door Mapping**: Repositories are randomly assigned to doors
4. **Rendering**: Raycasting engine draws 3D perspective
5. **Interaction**: Player opens doors to view repository READMEs

---

## Raycasting Rendering Engine

### What is Raycasting?

Raycasting is a rendering technique popularized by Wolfenstein 3D (1992). Unlike full 3D engines, it uses a 2D map to create a pseudo-3D perspective by casting rays from the player's position.

### Core Concepts

#### 1. The Player

```javascript
const player = {
    x: startX,           // Position in pixels
    y: startY,
    angle: 0,            // Viewing direction in radians
    speed: 3,            // Movement speed (pixels per frame)
    rotSpeed: 0.05       // Rotation speed (radians per frame)
};
```

#### 2. Field of View (FOV)

```javascript
const FOV = Math.PI / 3;           // 60 degrees
const HALF_FOV = FOV / 2;          // 30 degrees each side
const NUM_RAYS = 120;              // Resolution of rendering
const DELTA_ANGLE = FOV / NUM_RAYS; // Angle between rays
```

**Explanation**: The FOV determines how much of the world the player can see. We divide this into 120 rays, each representing one vertical slice of the screen.

```
        Player view cone:
              
              │
             ╱│╲
           ╱  │  ╲
         ╱    │    ╲
       ╱      │      ╲
     ╱   FOV  │  FOV   ╲
   ╱    30°   │   30°    ╱
 ╱____________│____________╱
      ← 120 rays →
```

### The Ray Casting Algorithm

#### Step 1: Cast a Single Ray

```javascript
function castRay(angle) {
    const rayX = Math.cos(angle);  // Ray direction X
    const rayY = Math.sin(angle);  // Ray direction Y
    
    let depth = 0;                 // Distance traveled
    let hit = false;               // Has ray hit a wall?
    let hitValue = 0;              // Type of wall hit
    
    const MAX_DEPTH = 800;         // Maximum ray length
    
    // March the ray forward until it hits something
    while (!hit && depth < MAX_DEPTH) {
        depth += 1;  // Step forward 1 pixel
        
        // Calculate target position
        const targetX = player.x + rayX * depth;
        const targetY = player.y + rayY * depth;
        
        // Check what's at this position
        hitValue = getMapValue(targetX, targetY);
        
        if (hitValue > 0) {  // 0 = empty, >0 = wall/door
            hit = true;
        }
    }
    
    return { depth, hitValue };
}
```

**How it works**:
1. Convert angle to direction vector using trigonometry
2. Step forward pixel by pixel along the ray
3. Check the map at each position
4. Stop when hitting a wall or reaching max distance

#### Step 2: Convert Map Coordinates

```javascript
function getMapValue(x, y) {
    // Convert pixel coordinates to tile coordinates
    const mx = Math.floor(x / TILE_SIZE);  // 64 pixels per tile
    const my = Math.floor(y / TILE_SIZE);
    
    // Check bounds
    if (mx < 0 || mx >= MAP_SIZE || my < 0 || my >= MAP_SIZE) {
        return 1;  // Treat out-of-bounds as wall
    }
    
    return map[my][mx];  // Return tile type
}
```

**Map values**:
- `0` = Empty space (walkable)
- `1` = Wall
- `2` = Door (repository portal)
- `5` = Exit

#### Step 3: Calculate Wall Height

```javascript
// After casting ray
const { depth, hitValue } = castRay(rayAngle);

// Fix fish-eye distortion
const distance = depth * Math.cos(rayAngle - player.angle);

// Calculate projected wall height
const wallHeight = (TILE_SIZE * HEIGHT) / (distance + 0.0001);
```

**Fish-eye correction**: Without the cosine correction, walls appear curved at screen edges because rays at angles travel further than center rays.

```
Without correction:        With correction:
    ╱──────╲                  │      │
   ╱        ╲                 │      │
  │  Curved  │                │Flat  │
   ╲        ╱                 │      │
    ╲──────╱                  │      │
```

#### Step 4: Draw the Wall Slice

```javascript
function drawWall(x, wallHeight, color, shade, hitValue) {
    // Apply distance-based shading
    const shadedColor = shadeColor(color, shade);
    
    ctx.fillStyle = shadedColor;
    
    // Draw vertical slice centered on screen
    ctx.fillRect(
        x,                              // X position
        (HEIGHT - wallHeight) / 2,      // Top Y (centered)
        WIDTH / NUM_RAYS + 1,           // Width of slice
        wallHeight                      // Height of slice
    );
    
    // Add text label for repository doors
    if (hitValue === 2 && wallHeight > 100) {
        ctx.fillStyle = '#000';
        ctx.font = 'bold 10px Courier New';
        ctx.textAlign = 'center';
        const textY = (HEIGHT - wallHeight) / 2 + wallHeight / 2;
        ctx.fillText('REPO', x + (WIDTH / NUM_RAYS) / 2, textY);
    }
}
```

#### Step 5: Distance-Based Shading

```javascript
function shadeColor(color, amount) {
    // Parse hex color to RGB
    const num = parseInt(color.slice(1), 16);
    const r = (num >> 16);        // Extract red
    const g = (num >> 8) & 0x00FF; // Extract green
    const b = num & 0x0000FF;      // Extract blue
    
    // Multiply by shade amount (0.3 to 1.0)
    return `rgb(${r * amount}, ${g * amount}, ${b * amount})`;
}

// Calculate shade based on distance
const shade = Math.max(0.3, 1 - distance / MAX_DEPTH);
```

**Effect**: Distant walls appear darker, creating depth perception.

### Complete Render Loop

```javascript
function render() {
    // 1. Draw ceiling (dark blue-gray)
    ctx.fillStyle = '#2C3E50';
    ctx.fillRect(0, 0, WIDTH, HEIGHT / 2);
    
    // 2. Draw floor (lighter gray)
    ctx.fillStyle = '#34495E';
    ctx.fillRect(0, HEIGHT / 2, WIDTH, HEIGHT / 2);
    
    // 3. Cast rays for each vertical slice
    for (let i = 0; i < NUM_RAYS; i++) {
        // Calculate ray angle
        const rayAngle = player.angle - HALF_FOV + (i * DELTA_ANGLE);
        
        // Cast the ray
        const { depth, hitValue } = castRay(rayAngle);
        
        // Calculate wall height with fish-eye correction
        const distance = depth * Math.cos(rayAngle - player.angle);
        const wallHeight = (TILE_SIZE * HEIGHT) / (distance + 0.0001);
        
        // Calculate shading
        const shade = Math.max(0.3, 1 - distance / MAX_DEPTH);
        
        // Get wall color
        const color = getWallColor(hitValue);
        
        // Draw this slice
        drawWall(i * (WIDTH / NUM_RAYS), wallHeight, color, shade, hitValue);
    }
}
```

### Player Movement

```javascript
function update(deltaTime) {
    const moveSpeed = player.speed;
    
    // Forward movement (W or Up Arrow)
    if (keys['w'] || keys['ArrowUp']) {
        const newX = player.x + Math.cos(player.angle) * moveSpeed;
        const newY = player.y + Math.sin(player.angle) * moveSpeed;
        
        // Only move if not colliding with wall
        if (!checkCollision(newX, newY)) {
            player.x = newX;
            player.y = newY;
        }
    }
    
    // Backward movement (S or Down Arrow)
    if (keys['s'] || keys['ArrowDown']) {
        const newX = player.x - Math.cos(player.angle) * moveSpeed;
        const newY = player.y - Math.sin(player.angle) * moveSpeed;
        
        if (!checkCollision(newX, newY)) {
            player.x = newX;
            player.y = newY;
        }
    }
    
    // Rotation (A/D or Arrow Keys)
    if (keys['a'] || keys['ArrowLeft']) {
        player.angle -= player.rotSpeed;
    }
    if (keys['d'] || keys['ArrowRight']) {
        player.angle += player.rotSpeed;
    }
}

function checkCollision(x, y) {
    const val = getMapValue(x, y);
    return val === 1 || val === 2;  // Wall or door blocks movement
}
```

---

## Procedural Map Generation

### Algorithm Overview

The map generation uses a **room-and-corridor** approach:

1. Generate random non-overlapping rooms
2. Connect all rooms using Minimum Spanning Tree (MST)
3. Add extra connections for loops
4. Place doors at room entrances
5. Place exit in a random room

### Data Structures

```python
class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x              # Top-left corner X
        self.y = y              # Top-left corner Y
        self.width = width      # Room width in tiles
        self.height = height    # Room height in tiles
        self.center = (x + width // 2, y + height // 2)  # Center point
```

### Step 1: Initialize Map Grid

```python
def generate_random_rooms(width: int = 154, height: int = 154, rooms_n: int = 20):
    # Create a grid filled with walls (1)
    map_grid = [[1 for _ in range(width)] for _ in range(height)]
    
    rooms = []
    max_attempts = 100
    room_count = rooms_n
```

**Map representation**: 2D array where each cell is a tile type.

### Step 2: Generate Random Rooms

```python
for _ in range(max_attempts):
    if len(rooms) >= room_count:
        break
    
    # Random room dimensions (4-8 tiles)
    room_w = random.randint(4, min(8, width - 4))
    room_h = random.randint(4, min(8, height - 4))
    
    # Random position with padding
    max_x = width - room_w - 2
    max_y = height - room_h - 2
    
    if max_x < 1 or max_y < 1:
        continue
    
    room_x = random.randint(1, max_x)
    room_y = random.randint(1, max_y)
    
    new_room = Room(room_x, room_y, room_w, room_h)
    
    # Check for overlaps with existing rooms
    overlaps = False
    for existing_room in rooms:
        if rooms_overlap(new_room, existing_room):
            overlaps = True
            break
    
    # Add room if it doesn't overlap
    if not overlaps:
        rooms.append(new_room)
```

#### Overlap Detection

```python
def rooms_overlap(room1: Room, room2: Room, padding: int = 2) -> bool:
    """Check if two rooms overlap with optional padding"""
    return (room1.x - padding < room2.x + room2.width + padding and
            room1.x + room1.width + padding > room2.x - padding and
            room1.y - padding < room2.y + room2.height + padding and
            room1.y + room1.height + padding > room2.y - padding)
```

**Visual example**:
```
  Room 1        Room 2 (overlaps)
┌────────┐    ┌────────┐
│        │    │        │
│    ┌───┼────┤        │
│    │   │    │        │
└────┼───┘    │        │
     └────────┘
     
  Room 1        Room 3 (no overlap)
┌────────┐      ┌────────┐
│        │      │        │
│        │      │        │
│        │      │        │
└────────┘      └────────┘
```

### Step 3: Carve Out Rooms

```python
# Convert wall tiles to floor tiles for each room
for room in rooms:
    for y in range(room.y, room.y + room.height):
        for x in range(room.x, room.x + room.width):
            if 0 <= y < height and 0 <= x < width:
                map_grid[y][x] = 0  # Floor tile
```

### Step 4: Connect Rooms (Minimum Spanning Tree)

The MST algorithm ensures all rooms are reachable with minimum corridor length.

```python
connected = set()      # Rooms already in the tree
unconnected = set(range(len(rooms)))  # Rooms not yet connected

# Start with a random room
start_idx = random.choice(list(unconnected))
connected.add(start_idx)
unconnected.remove(start_idx)

while unconnected:
    # Find closest unconnected room to any connected room
    closest_pair = None
    min_distance = float('inf')
    
    for connected_idx in connected:
        for unconnected_idx in unconnected:
            room1 = rooms[connected_idx]
            room2 = rooms[unconnected_idx]
            
            # Manhattan distance between centers
            dist = (abs(room1.center[0] - room2.center[0]) + 
                   abs(room1.center[1] - room2.center[1]))
            
            if dist < min_distance:
                min_distance = dist
                closest_pair = (connected_idx, unconnected_idx)
    
    if closest_pair:
        # Create corridor between the two rooms
        room1 = rooms[closest_pair[0]]
        room2 = rooms[closest_pair[1]]
        
        x1, y1 = room1.center
        x2, y2 = room2.center
        
        # Horizontal corridor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < width and 0 <= y1 < height:
                map_grid[y1][x] = 0
        
        # Vertical corridor
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x2 < width and 0 <= y < height:
                map_grid[y][x2] = 0
        
        # Mark room as connected
        connected.add(closest_pair[1])
        unconnected.remove(closest_pair[1])
```

**Visual example of MST**:
```
Initial state (4 rooms):

  ┌───┐           ┌───┐
  │ A │           │ B │
  └───┘           └───┘


         ┌───┐           ┌───┐
         │ C │           │ D │
         └───┘           └───┘

After MST connection:

  ┌───┐═══════════┌───┐
  │ A │           │ B │
  └───┘           └─║─┘
                    ║
         ┌───┐      ║   ┌───┐
         │ C │══════╝   │ D │
         └───┘           └───┘
```

### Step 5: Add Extra Connections (Create Loops)

```python
# Add some extra random connections for loops (40% chance)
if len(rooms) > 1:
    for i in range(len(rooms) // 2):
        room1, room2 = random.sample(rooms, 2)
        if random.random() < 0.4:
            x1, y1 = room1.center
            x2, y2 = room2.center
            
            # Create horizontal + vertical corridor
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < width and 0 <= y1 < height:
                    map_grid[y1][x] = 0
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x2 < width and 0 <= y < height:
                    map_grid[y][x2] = 0
```

**Why loops?** Makes exploration more interesting and provides alternate routes.

### Step 6: Place Doors

```python
door_positions = []

for room in rooms:
    # Check room perimeter for door positions
    for y in range(room.y - 1, room.y + room.height + 1):
        for x in range(room.x - 1, room.x + room.width + 1):
            if (0 < x < width - 1 and 0 < y < height - 1 and 
                map_grid[y][x] == 1):  # Wall tile
                
                # Check if wall has floor on exactly one side
                floor_count = 0
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < width and 0 <= ny < height and 
                        map_grid[ny][nx] == 0):
                        floor_count += 1
                
                # Valid door position: wall with floor on one side
                if floor_count == 1:
                    door_positions.append((x, y))

# Place doors (cap at rooms_n)
door_count = min(rooms_n, len(door_positions))
if door_count > 0:
    selected_doors = random.sample(door_positions, door_count)
    for x, y in selected_doors:
        map_grid[y][x] = 2  # Door tile
```

**Door placement logic**:
```
Invalid (floor on 2 sides):   Valid (floor on 1 side):
        
  ░░░ ░░░                      ░░░ ░░░
  ░░░■░░░                      ███■░░░
  ░░░ ░░░                      ███ ░░░
      
  ■ = potential door
  ░ = floor
  █ = wall
```

### Step 7: Place Exit

```python
if rooms:
    exit_room = random.choice(rooms)
    exit_x = exit_room.x + random.randint(1, max(1, exit_room.width - 1))
    exit_y = exit_room.y + random.randint(1, max(1, exit_room.height - 1))
    if 0 <= exit_x < width and 0 <= exit_y < height:
        map_grid[exit_y][exit_x] = 5  # Exit tile
```

### Finding Initial Player Position

```python
def initial_position(matrix):
    """Find first empty floor tile for player spawn"""
    for x in range(len(matrix)):
        for y in range(len(matrix[0])):
            if matrix[y][x] == 0:  # Floor tile
                return (x, y)
```

---

## GitHub API Integration

### Dual-Fetch Strategy

The system supports two methods to fetch GitHub data, with automatic fallback:

1. **Python `requests` library** (primary)
2. **GitHub CLI (`gh`)** (fallback)

### Repository Data Structure

```python
@dataclass
class Repository:
    """Data class to store repository information"""
    title: str                    # Repository name
    url: str                      # GitHub URL
    description: Optional[str]    # Short description
    readme: Optional[str] = None  # Full README content
```

### Class Structure

```python
class GitHubRepoFetcher:
    def __init__(self, username: str, cache_file: Optional[str] = None, 
                 max_workers: int = 10):
        self.username = username
        self.api_url = f"https://api.github.com/users/{username}/repos"
        self.cache_file = cache_file or f"data/{username}_repos.json"
        self.max_workers = max_workers  # Parallel README fetching
        self.print_lock = Lock()  # Thread-safe printing
```

### Method 1: Fetch with Requests

```python
def _fetch_with_requests(self) -> List[Repository]:
    """Fetch repositories using requests library"""
    
    # Step 1: Get all repository metadata (paginated)
    all_repos_data = []
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
        
        if not data:  # No more pages
            break
        
        all_repos_data.extend(data)
        page += 1
        
        if len(data) < per_page:  # Last page
            break
    
    print(f"Found {len(all_repos_data)} repositories")
    
    # Step 2: Fetch READMEs in parallel using ThreadPoolExecutor
    repos = []
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        # Submit all fetch tasks
        future_to_repo = {
            executor.submit(self._fetch_repo_with_readme, repo_data): repo_data
            for repo_data in all_repos_data
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_repo):
            try:
                repo = future.result()
                repos.append(repo)
            except Exception as e:
                repo_data = future_to_repo[future]
                print(f"Error processing {repo_data['name']}: {e}")
    
    return repos
```

### Fetching Individual READMEs

```python
def _fetch_readme(self, repo_name: str) -> Optional[str]:
    """Fetch README content for a repository"""
    readme_url = f"https://api.github.com/repos/{self.username}/{repo_name}/readme"
    
    try:
        response = requests.get(readme_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # GitHub returns README as base64-encoded content
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        else:
            return None
            
    except Exception as e:
        print(f"Failed to fetch README for {repo_name}: {e}")
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
```

### Method 2: Fetch with GitHub CLI

```python
def _fetch_with_gh_cli(self) -> List[Repository]:
    """Fetch repositories using gh CLI (fallback method)"""
    
    try:
        # Check if gh CLI is installed
        subprocess.run(['gh', '--version'], 
                      capture_output=True, 
                      check=True)
        
        # Fetch all repos with gh CLI
        result = subprocess.run(
            ['gh', 'repo', 'list', self.username, '--json', 
             'name,url,description', '--limit', '1000'],
            capture_output=True,
            text=True,
            check=True
        )
        
        all_repos_data = json.loads(result.stdout)
        
        # Fetch READMEs in parallel (same pattern as requests method)
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
                    print(f"Error processing {repo_data['name']}: {e}")
        
        return repos
        
    except FileNotFoundError:
        raise Exception("gh CLI not installed")
```

### README Fetching with CLI

```python
def _fetch_readme_with_gh_cli(self, repo_name: str) -> Optional[str]:
    """Fetch README using gh CLI, trying multiple filename variations"""
    
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
                ['gh', 'api', 
                 f'/repos/{self.username}/{repo_name}/contents/{readme_name}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            if 'content' in data:
                # Decode base64 content
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
                
        except subprocess.CalledProcessError:
            continue  # Try next variation
        except Exception as e:
            print(f"Error decoding README for {repo_name}: {e}")
            continue
    
    return None  # No README found
```

### Caching System

```python
def fetch_repos(self, force_refresh: bool = False) -> List[Repository]:
    """Main entry point with caching support"""
    
    # Check cache first
    if not force_refresh and os.path.exists(self.cache_file):
        print(f"Loading from cache: {self.cache_file}")
        return self._load_from_cache()
    
    # Fetch fresh data
    print(f"Fetching repositories for {self.username}...")
    
    try:
        repos = self._fetch_with_requests()
    except Exception as e:
        print(f"Failed with requests: {e}")
        print("Trying gh CLI...")
        repos = self._fetch_with_gh_cli()
    
    # Save to cache
    self._save_to_cache(repos)
    
    return repos

def _save_to_cache(self, repos: List[Repository]):
    """Save repositories to JSON cache file"""
    try:
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump([repo.to_dict() for repo in repos], 
                     f, indent=2, ensure_ascii=False)
        print(f"Saved {len(repos)} repositories to cache")
    except Exception as e:
        print(f"Failed to save cache: {e}")

def _load_from_cache(self) -> List[Repository]:
    """Load repositories from JSON cache file"""
    try:
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Repository.from_dict(repo) for repo in data]
    except Exception as e:
        raise Exception(f"Failed to load cache: {e}")
```

### Why Two Methods?

1. **Requests method**:
   - No external dependencies
   - Works with GitHub's public API
   - Rate limited (60 requests/hour unauthenticated)

2. **GitHub CLI method**:
   - Requires `gh` installation
   - Uses authenticated requests (higher rate limits)
   - More reliable for private repos

3. **Automatic fallback**: If one fails (network issues, rate limits), the other takes over

---

## Dynamic Door-to-Repository Mapping

### The Challenge

We need to:
1. Find all doors in the procedurally generated map
2. Assign each door to a random repository
3. Create a lookup system for interactions

### Step 1: Find All Doors

```javascript
// Door portal mapping object
const doorPortalMap = {};

// Find all doors (tile value 2) in the map
const doorPositions = [];

for (let y = 0; y < MAP_SIZE; y++) {
    for (let x = 0; x < MAP_SIZE; x++) {
        if (map[y][x] === 2) {  // Door tile
            doorPositions.push([x, y]);
        }
    }
}

console.log(`Found ${doorPositions.length} doors`);
```

### Step 2: Shuffle Door Positions

```javascript
// Fisher-Yates shuffle algorithm for randomness
for (let i = doorPositions.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    // Swap positions
    [doorPositions[i], doorPositions[j]] = [doorPositions[j], doorPositions[i]];
}
```

**Why shuffle?** Ensures repositories are distributed randomly across the map, making each playthrough feel different.

### Step 3: Assign Repositories to Doors

```javascript
// Map each door position to a repository index
doorPositions.forEach((pos, index) => {
    if (index < portalSites.length) {
        const [x, y] = pos;
        const key = `${x},${y}`;  // Create unique key "x,y"
        doorPortalMap[key] = index;  // Map to repository index
    }
});

console.log('Door mappings:', doorPortalMap);

// Example output:
// {
//   "23,45": 0,   // Door at (23,45) → Repository 0
//   "67,12": 1,   // Door at (67,12) → Repository 1
//   "89,34": 2,   // Door at (89,34) → Repository 2
//   ...
// }
```

### Step 4: Check What Player is Looking At

```javascript
function checkLookingAtDoor() {
    // Calculate direction player is facing
    const dirX = Math.cos(player.angle);
    const dirY = Math.sin(player.angle);
    const checkDist = 80;  // Check 80 pixels ahead
    
    // Calculate check position
    const checkX = player.x + dirX * checkDist;
    const checkY = player.y + dirY * checkDist;
    
    // Convert to tile coordinates
    const mx = Math.floor(checkX / TILE_SIZE);
    const my = Math.floor(checkY / TILE_SIZE);
    
    // Check if within bounds
    if (mx >= 0 && mx < MAP_SIZE && my >= 0 && my < MAP_SIZE) {
        const val = map[my][mx];
        
        // Is it a door?
        if (val === 2) {
            const doorKey = `${mx},${my}`;
            const portalIndex = doorPortalMap[doorKey];
            
            // Check if this door has a repository assigned
            if (portalIndex !== undefined) {
                return {
                    isDoor: true,
                    repoInfo: portalSites[portalIndex],
                    coords: doorKey
                };
            }
        }
    }
    
    return { isDoor: false };
}
```

**Visual explanation**:
```
Player view:
                 Check point (80px ahead)
                        ↓
    Player → → → → → [Door]
       ↑
    Facing direction
```

### Step 5: Interaction System

```javascript
function interact() {
    // Get player's facing direction
    const dirX = Math.cos(player.angle);
    const dirY = Math.sin(player.angle);
    const checkDist = 80;
    
    // Calculate check position
    const checkX = player.x + dirX * checkDist;
    const checkY = player.y + dirY * checkDist;
    
    // Convert to tile coordinates
    const mx = Math.floor(checkX / TILE_SIZE);
    const my = Math.floor(checkY / TILE_SIZE);
    const val = map[my][mx];
    
    // Check if it's a door
    if (val === 2) {
        const doorKey = `${mx},${my}`;
        const portalIndex = doorPortalMap[doorKey];
        
        if (portalIndex !== undefined) {
            // Open the repository README
            openReadme(portalSites[portalIndex]);
        }
    }
}

// Triggered by pressing 'E' key
window.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'e') {
        interact();
        keys['e'] = false;  // Prevent repeated triggers
    }
});
```

### Step 6: Display Door Information

```javascript
function update(deltaTime) {
    // ... movement code ...
    
    // Check if looking at door (throttled to every 100ms)
    const now = Date.now();
    if (now - lastDoorCheck > 100) {
        const doorCheck = checkLookingAtDoor();
        lookingAtDoor = doorCheck.isDoor;
        currentDoorInfo = doorCheck.isDoor ? doorCheck : null;
        lastDoorCheck = now;
    }
    
    // Update position display
    document.getElementById('pos').textContent = 
        `${Math.floor(player.x / TILE_SIZE)}, ${Math.floor(player.y / TILE_SIZE)}`;
}

function render() {
    // ... raycasting code ...
    
    // Show door information overlay if looking at a door
    if (lookingAtDoor && currentDoorInfo) {
        doorDescription.innerHTML = `
            <strong>${currentDoorInfo.repoInfo.title}</strong><br>
            ${currentDoorInfo.repoInfo.description}
        `;
        doorText.classList.add('show');  // Fade in
    } else {
        doorText.classList.remove('show');  // Fade out
    }
}
```

---

## README Display System

### Markdown Rendering

```javascript
// Global state
let readmeOpen = false;

// DOM elements
const readmeOverlay = document.getElementById('readme-overlay');
const readmeContent = document.getElementById('readme-content');
const closeBtn = document.getElementById('close-readme');
const repoTitle = document.getElementById('repo-title');
const readmeDescription = document.getElementById('readme-description');

// Event listeners
closeBtn.addEventListener('click', closeReadme);

function openReadme(repoInfo) {
    readmeOpen = true;
    readmeOverlay.classList.add('active');
    
    // Set repository title
    repoTitle.textContent = `📦 ${repoInfo.title}`;
    
    // Set description with link
    readmeDescription.innerHTML = `
        <strong>${repoInfo.title}</strong><br>
        ${repoInfo.description}<br>
        <a href="${repoInfo.url}" target="_blank" style="color: #FFD700;">
            ${repoInfo.url}
        </a>
    `;
    
    // Render markdown to HTML
    try {
        // Using marked.js library for markdown parsing
        readmeContent.innerHTML = marked.parse(repoInfo.readme);
    } catch (e) {
        // Fallback to plain text if markdown parsing fails
        readmeContent.innerHTML = `<pre>${repoInfo.readme}</pre>`;
    }
}

function closeReadme() {
    readmeOpen = false;
    readmeOverlay.classList.remove('active');
}

// ESC key to close
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && readmeOpen) {
        closeReadme();
    }
});
```

### Why Not iframes?

**Problem**: GitHub doesn't allow embedding their pages in iframes due to `X-Frame-Options: DENY` header.

**Solution**: 
1. Fetch README markdown content via API
2. Render markdown to HTML using `marked.js`
3. Display in a styled overlay

**Benefits**:
- Full control over styling
- No CORS issues
- Works offline with cached data
- Better performance

### Pausing Game During README View

```javascript
function gameLoop(timestamp) {
    // Skip rendering if README is open
    if (readmeOpen) {
        requestAnimationFrame(gameLoop);
        return;  // Don't update game state
    }
    
    const deltaTime = timestamp - lastTime;
    lastTime = timestamp;
    
    // Calculate FPS
    frameCount++;
    fpsTime += deltaTime;
    if (fpsTime >= 1000) {
        fps = Math.round(frameCount * 1000 / fpsTime);
        document.getElementById('fps').textContent = fps;
        frameCount = 0;
        fpsTime = 0;
    }
    
    // Update game state
    update(deltaTime);
    
    // Render 3D view
    render();
    
    // Draw minimap
    drawMinimap();
    
    // Continue loop
    requestAnimationFrame(gameLoop);
}
```

---

## Minimap System

### Purpose

The minimap provides a top-down 2D view of the entire map, showing:
- Walls (white)
- Doors/Repositories (yellow)
- Floor (dark gray)
- Player position (red dot)
- Player direction (red line)

### Implementation

```javascript
function drawMinimap() {
    // Calculate scale factor
    const scale = minimap.width / (MAP_SIZE * TILE_SIZE);
    
    // Clear minimap
    mmCtx.fillStyle = '#000';
    mmCtx.fillRect(0, 0, minimap.width, minimap.height);
    
    // Draw map tiles
    for (let y = 0; y < MAP_SIZE; y++) {
        for (let x = 0; x < MAP_SIZE; x++) {
            const val = map[y][x];
            
            // Set color based on tile type
            if (val === 1) {
                mmCtx.fillStyle = '#fff';  // Wall = white
            } else if (val === 2) {
                mmCtx.fillStyle = '#ff0';  // Door = yellow
            } else {
                mmCtx.fillStyle = '#222';  // Floor = dark gray
            }
            
            // Draw scaled tile
            mmCtx.fillRect(
                x * TILE_SIZE * scale,
                y * TILE_SIZE * scale,
                TILE_SIZE * scale,
                TILE_SIZE * scale
            );
        }
    }
    
    // Draw player position
    mmCtx.fillStyle = '#f00';  // Red
    mmCtx.beginPath();
    mmCtx.arc(
        player.x * scale,     // Scaled X position
        player.y * scale,     // Scaled Y position
        3,                    // Radius
        0,
        Math.PI * 2
    );
    mmCtx.fill();
    
    // Draw direction indicator
    mmCtx.strokeStyle = '#f00';
    mmCtx.beginPath();
    mmCtx.moveTo(player.x * scale, player.y * scale);
    mmCtx.lineTo(
        player.x * scale + Math.cos(player.angle) * 15,
        player.y * scale + Math.sin(player.angle) * 15
    );
    mmCtx.stroke();
}
```

**Visual representation**:
```
Minimap (200x200 canvas):

┌────────────────────────┐
│███████████████████████ │  ███ = Wall
│█░░░░░░░░░░░░░░░░░░░░█ │  ░░░ = Floor
│█░██████░░░░░░██████░░█ │  ⚫→ = Player
│█░█⚫→█░░░░░░░░█    █░█ │  🟡 = Door/Repo
│█░█🟡  █░░░░░░░██████░█ │
│█░████████░░░░░░░░░░░░█ │
│█░░░░░░░░░░░░░░░░░░░░█ │
│███████████████████████ │
└────────────────────────┘
```

---

## Performance Optimization

### FPS Counter

```javascript
let fps = 0;
let lastTime = 0;
let frameCount = 0;
let fpsTime = 0;

function gameLoop(timestamp) {
    const deltaTime = timestamp - lastTime;
    lastTime = timestamp;
    
    // Accumulate frames
    frameCount++;
    fpsTime += deltaTime;
    
    // Update FPS display every second
    if (fpsTime >= 1000) {
        fps = Math.round(frameCount * 1000 / fpsTime);
        document.getElementById('fps').textContent = fps;
        
        // Reset counters
        frameCount = 0;
        fpsTime = 0;
    }
    
    // ... rest of game loop
}
```

### Optimization Techniques

#### 1. Raycasting Resolution

```javascript
const NUM_RAYS = 120;  // Lower = faster, but blockier
                       // Higher = slower, but smoother
```

**Trade-off**:
- 60 rays: Very fast, visible slices
- 120 rays: Balanced (default)
- 240 rays: Smooth, may lag on slow devices

#### 2. Maximum Ray Distance

```javascript
const MAX_DEPTH = 800;  // Stop rays early to save computation
```

**Effect**: Distant walls not rendered, but saves significant processing.

#### 3. Throttled Door Checking

```javascript
let lastDoorCheck = 0;

// Only check every 100ms instead of every frame
if (now - lastDoorCheck > 100) {
    const doorCheck = checkLookingAtDoor();
    // ... update state
    lastDoorCheck = now;
}
```

**Savings**: Reduces collision checks from 60/second to 10/second.

#### 4. Early Ray Termination

```javascript
while (!hit && depth < MAX_DEPTH) {
    depth += 1;
    const targetX = player.x + rayX * depth;
    const targetY = player.y + rayY * depth;
    
    hitValue = getMapValue(targetX, targetY);
    
    if (hitValue > 0) {
        hit = true;  // Stop immediately when hitting wall
        break;
    }
}
```

---

## Complete System Integration

### Backend Flow (Python/Flask)

```python
from flask import Flask, render_template
from fetch_repos import GitHubRepoFetcher
from map_generator import generate_random_rooms, initial_position

app = Flask(__name__)

@app.route('/')
def index():
    # 1. Fetch repositories (cached)
    fetcher = GitHubRepoFetcher('username')
    repos = fetcher.fetch_repos(force_refresh=False)
    
    # 2. Generate procedural map
    map_size = 154
    num_doors = len(repos)
    map_grid = generate_random_rooms(
        width=map_size,
        height=map_size,
        rooms_n=num_doors
    )
    
    # 3. Find player spawn position
    x, y = initial_position(map_grid)
    
    # 4. Convert repos to JSON-serializable format
    repos_data = [repo.to_dict() for repo in repos]
    
    # 5. Render template with data
    return render_template(
        'index.html',
        map=map_grid,
        x=x,
        y=y,
        map_size=map_size,
        repos_data=repos_data
    )

if __name__ == '__main__':
    app.run(debug=True)
```

### Template Integration (Jinja2)

```html
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Museum</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
    <canvas id="canvas" width="800" height="600"></canvas>
    <canvas id="minimap" width="200" height="200"></canvas>
    
    <div id="hud">
        <div>FPS: <span id="fps">0</span></div>
        <div>Position: <span id="pos">0, 0</span></div>
        <div>Repositories: <span id="repo-count">0</span></div>
    </div>
    
    <div id="door-text" class="door-prompt">
        <div id="door-description"></div>
        <div>Press E to view repository</div>
    </div>
    
    <div id="readme-overlay">
        <div class="readme-container">
            <div class="readme-header">
                <h2 id="repo-title"></h2>
                <button id="close-readme">✕</button>
            </div>
            <div id="readme-description"></div>
            <div id="readme-content"></div>
        </div>
    </div>
    
    <script>
        // Data injected from backend
        const backendRepos = {{ repos_data | tojson | safe }};
        const map = {{ map | tojson | safe }};
        
        // ... game engine code ...
    </script>
</body>
</html>
```

---

## Advanced Concepts

### 1. DDA Algorithm (Alternative to Naive Raycasting)

The current implementation uses naive raycasting (stepping 1 pixel at a time). For better performance, you can implement Digital Differential Analyzer (DDA):

```javascript
function castRayDDA(angle) {
    const rayX = Math.cos(angle);
    const rayY = Math.sin(angle);
    
    let mapX = Math.floor(player.x / TILE_SIZE);
    let mapY = Math.floor(player.y / TILE_SIZE);
    
    // Calculate step direction
    const stepX = rayX > 0 ? 1 : -1;
    const stepY = rayY > 0 ? 1 : -1;
    
    // Calculate distance to next tile boundary
    const deltaDistX = Math.abs(1 / rayX);
    const deltaDistY = Math.abs(1 / rayY);
    
    let sideDistX = rayX > 0
        ? ((mapX + 1) * TILE_SIZE - player.x) / TILE_SIZE * deltaDistX
        : (player.x - mapX * TILE_SIZE) / TILE_SIZE * deltaDistX;
    
    let sideDistY = rayY > 0
        ? ((mapY + 1) * TILE_SIZE - player.y) / TILE_SIZE * deltaDistY
        : (player.y - mapY * TILE_SIZE) / TILE_SIZE * deltaDistY;
    
    let hit = false;
    let side;  // 0 = X side, 1 = Y side
    
    // Step through tiles until hitting a wall
    while (!hit) {
        // Jump to next tile boundary
        if (sideDistX < sideDistY) {
            sideDistX += deltaDistX;
            mapX += stepX;
            side = 0;
        } else {
            sideDistY += deltaDistY;
            mapY += stepY;
            side = 1;
        }
        
        // Check if hit wall
        const val = map[mapY]?.[mapX];
        if (val > 0) {
            hit = true;
        }
    }
    
    // Calculate distance
    const distance = side === 0
        ? (sideDistX - deltaDistX)
        : (sideDistY - deltaDistY);
    
    return { 
        depth: distance * TILE_SIZE, 
        hitValue: map[mapY][mapX],
        side 
    };
}
```

**Advantage**: Jumps from tile to tile instead of checking every pixel, ~10x faster.

### 2. Texture Mapping

To add textures to walls:

```javascript
// Load texture image
const wallTexture = new Image();
wallTexture.src = 'wall_texture.png';

function drawTexturedWall(x, wallHeight, texture, textureX) {
    const wallTop = (HEIGHT - wallHeight) / 2;
    
    // Draw thin vertical slice from texture
    ctx.drawImage(
        texture,
        textureX, 0,              // Source X, Y
        1, texture.height,        // Source width, height
        x, wallTop,               // Dest X, Y
        WIDTH / NUM_RAYS + 1,     // Dest width
        wallHeight                // Dest height
    );
}
```

### 3. Sprite Rendering (For NPCs/Objects)

```javascript
function renderSprite(spriteX, spriteY, spriteTexture) {
    // Transform sprite position to player coordinate system
    const dx = spriteX - player.x;
    const dy = spriteY - player.y;
    
    const invDet = 1.0 / (Math.cos(player.angle) * Math.sin(player.angle + Math.PI/2) - 
                          Math.sin(player.angle) * Math.cos(player.angle + Math.PI/2));
    
    const transformX = invDet * (Math.sin(player.angle + Math.PI/2) * dx - 
                                 Math.cos(player.angle + Math.PI/2) * dy);
    const transformY = invDet * (-Math.sin(player.angle) * dx + 
                                 Math.cos(player.angle) * dy);
    
    // Calculate sprite screen position
    const spriteScreenX = (WIDTH / 2) * (1 + transformX / transformY);
    
    // Calculate sprite height
    const spriteHeight = Math.abs(HEIGHT / transformY);
    
    // Draw sprite
    ctx.drawImage(
        spriteTexture,
        spriteScreenX - spriteHeight / 2,
        (HEIGHT - spriteHeight) / 2,
        spriteHeight,
        spriteHeight
    );
}
```

### 4. Floor/Ceiling Casting

For textured floors:

```javascript
function renderFloorCeiling() {
    for (let y = HEIGHT / 2; y < HEIGHT; y++) {
        // Ray direction for leftmost and rightmost ray
        const rayDirX0 = Math.cos(player.angle - HALF_FOV);
        const rayDirY0 = Math.sin(player.angle - HALF_FOV);
        const rayDirX1 = Math.cos(player.angle + HALF_FOV);
        const rayDirY1 = Math.sin(player.angle + HALF_FOV);
        
        // Vertical position of the row on screen
        const p = y - HEIGHT / 2;
        const posZ = 0.5 * HEIGHT;
        const rowDistance = posZ / p;
        
        // Calculate floor position
        const floorStepX = rowDistance * (rayDirX1 - rayDirX0) / WIDTH;
        const floorStepY = rowDistance * (rayDirY1 - rayDirY0) / WIDTH;
        
        let floorX = player.x + rowDistance * rayDirX0;
        let floorY = player.y + rowDistance * rayDirY0;
        
        for (let x = 0; x < WIDTH; x++) {
            // Sample floor texture
            const cellX = Math.floor(floorX / TILE_SIZE);
            const cellY = Math.floor(floorY / TILE_SIZE);
            
            const tx = Math.floor((floorX % TILE_SIZE) * floorTexture.width / TILE_SIZE);
            const ty = Math.floor((floorY % TILE_SIZE) * floorTexture.height / TILE_SIZE);
            
            // Draw floor pixel
            const color = getTexturePixel(floorTexture, tx, ty);
            ctx.fillStyle = color;
            ctx.fillRect(x, y, 1, 1);
            
            floorX += floorStepX;
            floorY += floorStepY;
        }
    }
}
```

---

## Troubleshooting Guide

### Issue: Low FPS

**Solutions**:
1. Reduce `NUM_RAYS` (e.g., 60 instead of 120)
2. Decrease `MAX_DEPTH` (e.g., 500 instead of 800)
3. Increase door check throttle (200ms instead of 100ms)

### Issue: Doors Not Showing Repos

**Check**:
```javascript
console.log('Door positions found:', doorPositions.length);
console.log('Repositories loaded:', portalSites.length);
console.log('Door mappings:', doorPortalMap);
```

**Common cause**: More doors than repositories. The extra doors won't have mappings.

### Issue: README Not Rendering

**Solutions**:
1. Check if `marked.js` is loaded
2. Verify README content exists: `console.log(repo.readme)`
3. Check browser console for markdown parsing errors

### Issue: Player Stuck in Walls

**Cause**: Spawn position on wall tile

**Fix**:
```python
def initial_position(matrix):
    # Ensure we find a floor tile (value 0)
    for y in range(len(matrix)):
        for x in range(len(matrix[0])):
            if matrix[y][x] == 0:
                return (x, y)
    # Fallback
    return (1, 1)
```

---

## Deployment Considerations

### 1. GitHub API Rate Limits

**Unauthenticated**: 60 requests/hour  
**Authenticated**: 5,000 requests/hour

**Solution**: Always use caching:
```python
fetcher = GitHubRepoFetcher('username', cache_file='repos_cache.json')
repos = fetcher.fetch_repos(force_refresh=False)
```

### 2. Large README Performance

**Problem**: Some READMEs are very large (100KB+)

**Solution**: Truncate in backend:
```python
MAX_README_SIZE = 50000  # 50KB

if repo.readme and len(repo.readme) > MAX_README_SIZE:
    repo.readme = repo.readme[:MAX_README_SIZE] + "\n\n... (truncated)"
```

### 3. Mobile Support

**Add touch controls**:
```javascript
let touchStartX = 0;
let touchStartY = 0;

canvas.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
});

canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const dx = e.touches[0].clientX - touchStartX;
    const dy = e.touches[0].clientY - touchStartY;
    
    // Rotation
    player.angle += dx * 0.01;
    
    // Movement
    if (Math.abs(dy) > 10) {
        const moveDir = dy > 0 ? -1 : 1;
        const newX = player.x + Math.cos(player.angle) * moveDir * player.speed;
        const newY = player.y + Math.sin(player.angle) * moveDir * player.speed;
        
        if (!checkCollision(newX, newY)) {
            player.x = newX;
            player.y = newY;
        }
    }
    
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
});
```

---

## Extending the Museum

### Ideas for Enhancement in future

1. **Multi-floor dungeons**: Staircases to different levels
2. **Gallery categories**: Group repos by language/topic
3. **Visitor counter**: Track which repos are most viewed
4. **Curator notes**: Add custom descriptions
5. **Search system**: Find specific repositories
6. **Collaborative mode**: Multiple players explore together
7. **Dynamic lighting**: Torches, spotlights on featured projects
8. **Achievement system**: Badges for exploring all repos

### Example: Adding a Lighting System

```javascript
function calculateLighting(distance, baseColor) {
    const maxBrightness = 1.0;
    const minBrightness = 0.2;
    const falloffDistance = 300;
    
    // Exponential falloff
    const brightness = Math.max(
        minBrightness,
        maxBrightness * Math.exp(-distance / falloffDistance)
    );
    
    return shadeColor(baseColor, brightness);
}
```

---

## Conclusion

This GitHub museum combines several classic computer graphics techniques:

1. **Raycasting**: Fast pseudo-3D rendering
2. **Procedural generation**: Unique maps every time
3. **API integration**: Dynamic content from GitHub
4. **Markdown rendering**: Formatted documentation display

The system demonstrates how retro game techniques can create novel ways to explore modern data. By treating repositories as art pieces in a virtual space, it transforms code browsing into an interactive, gamified experience.

### Key Takeaways

- **Raycasting is efficient**: Thousands of calculations per frame, yet runs smoothly
- **Procedural generation adds replay value**: Every session feels different
- **API fallbacks improve reliability**: Dual-fetch strategy handles failures
- **Caching is essential**: Respects rate limits and improves performance
- **Markdown rendering solves iframe limitations**: Full control over presentation

### Further Reading

- **Game Engine Architecture** by Jason Gregory
- **Tricks of the Game Programming Gurus** (Wolfenstein techniques)
- **GitHub API Documentation**: https://docs.github.com/en/rest
- **Procedural Generation in Game Design** by Tanya X. Short

### Future work

- **algorithm**: for sort most important Repos
- **AI**:" generate images acording to the repo
- **automatic**: github readme creator
---

*Happy museum building! May your repositories be ever on display.* 🎨🖼️
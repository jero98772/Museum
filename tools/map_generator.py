import random
from typing import List, Tuple, Set

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = (x + width // 2, y + height // 2)

class BSPNode:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left = None
        self.right = None
        self.room = None
        
    def split(self, min_size: int = 5) -> bool:
        """Split the node into two children"""
        if self.left or self.right:
            return False
            
        # Decide split direction based on aspect ratio
        split_horizontal = random.choice([True, False])
        if self.width > self.height and self.width / self.height >= 1.25:
            split_horizontal = False
        elif self.height > self.width and self.height / self.width >= 1.25:
            split_horizontal = True
            
        max_size = (self.height if split_horizontal else self.width) - min_size
        if max_size <= min_size:
            return False
            
        split_pos = random.randint(min_size, max_size)
        
        if split_horizontal:
            self.left = BSPNode(self.x, self.y, self.width, split_pos)
            self.right = BSPNode(self.x, self.y + split_pos, self.width, self.height - split_pos)
        else:
            self.left = BSPNode(self.x, self.y, split_pos, self.height)
            self.right = BSPNode(self.x + split_pos, self.y, self.width - split_pos, self.height)
            
        return True

def generate_bsp_tree(root: BSPNode, iterations: int, min_size: int = 5):
    """Recursively split the BSP tree"""
    if iterations > 0:
        if root.split(min_size):
            generate_bsp_tree(root.left, iterations - 1, min_size)
            generate_bsp_tree(root.right, iterations - 1, min_size)

def create_rooms(node: BSPNode, min_room_size: int = 3):
    """Create rooms in leaf nodes"""
    if node.left or node.right:
        if node.left:
            create_rooms(node.left, min_room_size)
        if node.right:
            create_rooms(node.right, min_room_size)
    else:
        # Create a room in this leaf
        room_width = random.randint(min_room_size, max(min_room_size, node.width - 2))
        room_height = random.randint(min_room_size, max(min_room_size, node.height - 2))
        room_x = node.x + random.randint(1, node.width - room_width - 1)
        room_y = node.y + random.randint(1, node.height - room_height - 1)
        node.room = Room(room_x, room_y, room_width, room_height)

def get_all_rooms(node: BSPNode) -> List[Room]:
    """Get all rooms from the BSP tree"""
    rooms = []
    if node.room:
        rooms.append(node.room)
    if node.left:
        rooms.extend(get_all_rooms(node.left))
    if node.right:
        rooms.extend(get_all_rooms(node.right))
    return rooms

def create_corridor(map_grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]):
    """Create L-shaped corridor between two points"""
    x1, y1 = start
    x2, y2 = end
    
    # Horizontal then vertical
    if random.choice([True, False]):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if map_grid[y1][x] == 1:
                map_grid[y1][x] = 0
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if map_grid[y][x2] == 1:
                map_grid[y][x2] = 0
    else:  # Vertical then horizontal
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if map_grid[y][x1] == 1:
                map_grid[y][x1] = 0
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if map_grid[y2][x] == 1:
                map_grid[y2][x] = 0

def connect_rooms(node: BSPNode, map_grid: List[List[int]]):
    """Recursively connect rooms through corridors"""
    if node.left and node.right:
        connect_rooms(node.left, map_grid)
        connect_rooms(node.right, map_grid)
        
        # Get rooms from both children
        left_rooms = get_all_rooms(node.left)
        right_rooms = get_all_rooms(node.right)
        
        if left_rooms and right_rooms:
            room1 = random.choice(left_rooms)
            room2 = random.choice(right_rooms)
            create_corridor(map_grid, room1.center, room2.center)

def is_connected_dfs(map_grid: List[List[int]]) -> bool:
    """Check if all walkable spaces are connected using DFS"""
    height = len(map_grid)
    width = len(map_grid[0])
    
    # Find first walkable cell
    start = None
    walkable_count = 0
    for y in range(height):
        for x in range(width):
            if map_grid[y][x] != 1:
                walkable_count += 1
                if start is None:
                    start = (x, y)
    
    if start is None:
        return False
    
    # DFS to count reachable cells
    visited = set()
    stack = [start]
    
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        
        # Check 4 directions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if map_grid[ny][nx] != 1 and (nx, ny) not in visited:
                    stack.append((nx, ny))
    
    return len(visited) == walkable_count

def generate_map(width: int = 16, height: int = 16, n_doors: int = 3) -> List[List[int]]:
    """Generate a BSP dungeon map with n doors (2s)"""
    # Initialize map with walls
    map_grid = [[1 for _ in range(width)] for _ in range(height)]
    
    # Create BSP tree
    root = BSPNode(1, 1, width - 2, height - 2)
    generate_bsp_tree(root, iterations=4, min_size=4)
    create_rooms(root, min_room_size=3)
    
    # Get all rooms
    rooms = get_all_rooms(root)
    
    # Carve out rooms
    for room in rooms:
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                map_grid[y][x] = 0
    
    # Connect rooms with corridors
    connect_rooms(root, map_grid)
    
    # Verify connectivity
    if not is_connected_dfs(map_grid):
        # If not connected, try again
        return generate_map(width, height, n_doors)
    
    # Place doors (2s) at corridor-room junctions
    door_positions = []
    for room in rooms:
        # Check room perimeter for potential door locations
        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if 0 < x < width - 1 and 0 < y < height - 1:
                    # Check if it's a wall between room and corridor
                    if map_grid[y][x] == 1:
                        adjacent_floor = 0
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height and map_grid[ny][nx] == 0:
                                adjacent_floor += 1
                        if adjacent_floor >= 2:
                            door_positions.append((x, y))
    
    # Place n doors randomly
    if len(door_positions) >= n_doors:
        selected_doors = random.sample(door_positions, n_doors)
        for x, y in selected_doors:
            map_grid[y][x] = 2
    
    # Place exit (5) in a random room
    if rooms:
        exit_room = random.choice(rooms)
        exit_x = exit_room.x + random.randint(0, exit_room.width - 1)
        exit_y = exit_room.y + random.randint(0, exit_room.height - 1)
        map_grid[exit_y][exit_x] = 5
    
    return map_grid

# Example usage
if __name__ == "__main__":
    map_data = generate_map(width=16, height=16, n_doors=3)
    
    # Print the map
    for row in map_data:
        print(row)
    
    print("\nMap Legend:")
    print("1 = Wall")
    print("0 = Floor")
    print("2 = Door")
    print("5 = Exit")
    
    # Verify connectivity
    print(f"\nAll spaces connected: {is_connected_dfs(map_data)}")
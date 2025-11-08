import random
from typing import List, Tuple

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = (x + width // 2, y + height // 2)

def rooms_overlap(room1: Room, room2: Room, padding: int = 2) -> bool:
    """Check if two rooms overlap with optional padding"""
    return (room1.x - padding < room2.x + room2.width + padding and
            room1.x + room1.width + padding > room2.x - padding and
            room1.y - padding < room2.y + room2.height + padding and
            room1.y + room1.height + padding > room2.y - padding)

def generate_random_rooms(width: int = 154, height: int = 154, rooms_n: int = 20) -> List[List[int]]:
    """Generate a map with randomly placed non-overlapping rooms"""
    map_grid = [[1 for _ in range(width)] for _ in range(height)]
    
    rooms = []
    max_attempts = 100
    room_count = rooms_n# random.randint(min_rooms, max_rooms)
    
    for _ in range(max_attempts):
        if len(rooms) >= room_count:
            break
            
        # Random room size
        room_w = random.randint(4, 8)
        room_h = random.randint(4, 8)
        
        # Random position with border padding
        room_x = random.randint(1, width - room_w - 2)
        room_y = random.randint(1, height - room_h - 2)
        
        new_room = Room(room_x, room_y, room_w, room_h)
        
        # Check for overlaps
        overlaps = False
        for existing_room in rooms:
            if rooms_overlap(new_room, existing_room):
                overlaps = True
                break
                
        if not overlaps:
            rooms.append(new_room)
    
    # Carve out rooms
    for room in rooms:
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                map_grid[y][x] = 0
    
    # Create minimum spanning tree to connect all rooms
    connected = set()
    unconnected = set(range(len(rooms)))
    
    if rooms:
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
                    dist = abs(room1.center[0] - room2.center[0]) + abs(room1.center[1] - room2.center[1])
                    
                    if dist < min_distance:
                        min_distance = dist
                        closest_pair = (connected_idx, unconnected_idx)
            
            if closest_pair:
                # Connect the rooms
                room1 = rooms[closest_pair[0]]
                room2 = rooms[closest_pair[1]]
                
                # Create corridor between centers
                x1, y1 = room1.center
                x2, y2 = room2.center
                
                # Horizontal then vertical
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    map_grid[y1][x] = 0
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    map_grid[y][x2] = 0
                
                connected.add(closest_pair[1])
                unconnected.remove(closest_pair[1])
    
    # Add some extra random connections for loops
    for i in range(len(rooms) // 2):
        room1, room2 = random.sample(rooms, 2)
        if random.random() < 0.4:  # 40% chance for extra connection
            x1, y1 = room1.center
            x2, y2 = room2.center
            
            for x in range(min(x1, x2), max(x1, x2) + 1):
                map_grid[y1][x] = 0
            for y in range(min(y1, y2), max(y1, y2) + 1):
                map_grid[y][x2] = 0
    
    # Add doors
    door_positions = []
    for room in rooms:
        # Check room perimeter for door positions
        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if (0 < x < width - 1 and 0 < y < height - 1 and 
                    map_grid[y][x] == 1):
                    # Check if wall has floor on exactly one side (door candidate)
                    floor_count = 0
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height and map_grid[ny][nx] == 0:
                            floor_count += 1
                    
                    if floor_count == 1:
                        door_positions.append((x, y))
    
    # Place 3-5 doors
    door_count = rooms_n #random.randint(3, 5)
    if len(door_positions) > door_count:
        selected_doors = random.sample(door_positions, door_count)
        for x, y in selected_doors:
            map_grid[y][x] = 2
    
    # Place exit
    if rooms:
        exit_room = random.choice(rooms)
        exit_x = exit_room.x + random.randint(1, exit_room.width - 1)
        exit_y = exit_room.y + random.randint(1, exit_room.height - 1)
        map_grid[exit_y][exit_x] = 5
    
    return map_grid

def initial_position(matrix):
    for x in range(len(matrix)):
        for y in range(len(matrix[0])):
            if matrix[y][x] == 0:
                return (x,y) 


# Example usage and visualization

'''
if __name__ == "__main__":
    print("\nRandom Room Layout:")
    x=173
    mid=173//2
    random_map = generate_random_rooms(mid, mid,min_rooms=x, max_rooms=x)
    for row in random_map:
        print(''.join(str(cell) for cell in row))


    print(type(random_map))
    print(initial_position(random_map))
'''

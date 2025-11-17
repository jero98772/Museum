        const keys = {};
        const FOV = Math.PI / 3;
        const HALF_FOV = FOV / 2;
        const NUM_RAYS = 120;
        const MAX_DEPTH = 800;
        const DELTA_ANGLE = FOV / NUM_RAYS;
        
        let fps = 0;
        let lastTime = 0;
        let frameCount = 0;
        let fpsTime = 0;
        
        let lookingAtDoor = false;
        let currentDoorInfo = null;
        let lastDoorCheck = 0;
        
        // Portal state
        let readmeOpen = false;
        const readmeOverlay = document.getElementById('readme-overlay');
        const readmeContent = document.getElementById('readme-content');
        const closeBtn = document.getElementById('close-readme');
        const doorText = document.getElementById('door-text');
        const doorDescription = document.getElementById('door-description');
        const repoTitle = document.getElementById('repo-title');
        const readmeDescription = document.getElementById('readme-description');
        
        closeBtn.addEventListener('click', closeReadme);
        
        function closeReadme() {
            readmeOpen = false;
            readmeOverlay.classList.remove('active');
        }
        
        function openReadme(repoInfo) {
            readmeOpen = true;
            readmeOverlay.classList.add('active');
            
            // Set title and description
            repoTitle.textContent = `📦 ${repoInfo.title}`;
            readmeDescription.innerHTML = `
                <strong>${repoInfo.title}</strong><br>
                ${repoInfo.description}<br>
                <a href="${repoInfo.url}" target="_blank" style="color: #FFD700;">${repoInfo.url}</a>
            `;
            
            // Render markdown
            try {
                readmeContent.innerHTML = marked.parse(repoInfo.readme);
            } catch (e) {
                readmeContent.innerHTML = `<pre>${repoInfo.readme}</pre>`;
            }
        }
        
        function getMapValue(x, y) {
            const mx = Math.floor(x / TILE_SIZE);
            const my = Math.floor(y / TILE_SIZE);
            if (mx < 0 || mx >= MAP_SIZE || my < 0 || my >= MAP_SIZE) return 1;
            return map[my][mx];
        }
        
        function checkCollision(x, y) {
            const val = getMapValue(x, y);
            return val === 1 || val === 2;
        }
        
        function checkLookingAtDoor() {
            const dirX = Math.cos(player.angle);
            const dirY = Math.sin(player.angle);
            const checkDist = 80;
            
            const checkX = player.x + dirX * checkDist;
            const checkY = player.y + dirY * checkDist;
            
            const mx = Math.floor(checkX / TILE_SIZE);
            const my = Math.floor(checkY / TILE_SIZE);
            
            if (mx >= 0 && mx < MAP_SIZE && my >= 0 && my < MAP_SIZE) {
                const val = map[my][mx];
                if (val === 2) {
                    const doorKey = `${mx},${my}`;
                    const portalIndex = doorPortalMap[doorKey];
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
        
        function interact() {
            const dirX = Math.cos(player.angle);
            const dirY = Math.sin(player.angle);
            const checkDist = 80;
            
            const checkX = player.x + dirX * checkDist;
            const checkY = player.y + dirY * checkDist;
            
            const mx = Math.floor(checkX / TILE_SIZE);
            const my = Math.floor(checkY / TILE_SIZE);
            const val = map[my][mx];
            
            if (val === 2) {
                // Open repository README
                const doorKey = `${mx},${my}`;
                const portalIndex = doorPortalMap[doorKey];
                if (portalIndex !== undefined) {
                    openReadme(portalSites[portalIndex]);
                }
            }
        }
        
        function castRay(angle) {
            const rayX = Math.cos(angle);
            const rayY = Math.sin(angle);
            
            let depth = 0;
            let hit = false;
            let hitValue = 0;
            
            while (!hit && depth < MAX_DEPTH) {
                depth += 1;
                const targetX = player.x + rayX * depth;
                const targetY = player.y + rayY * depth;
                
                hitValue = getMapValue(targetX, targetY);
                if (hitValue > 0) {
                    hit = true;
                }
            }
            
            return { depth, hitValue };
        }
        
        function drawWall(x, wallHeight, color, shade, hitValue) {
            const shadedColor = shadeColor(color, shade);
            ctx.fillStyle = shadedColor;
            ctx.fillRect(x, (HEIGHT - wallHeight) / 2, WIDTH / NUM_RAYS + 1, wallHeight);
            
            // Draw text on repository doors
            if (hitValue === 2 && wallHeight > 100) {
                ctx.fillStyle = '#000';
                ctx.font = 'bold 10px Courier New';
                ctx.textAlign = 'center';
                const textY = (HEIGHT - wallHeight) / 2 + wallHeight / 2;
                ctx.fillText('REPO', x + (WIDTH / NUM_RAYS) / 2, textY);
            }
        }
        
        function shadeColor(color, amount) {
            const num = parseInt(color.slice(1), 16);
            const r = Math.max(0, Math.min(255, (num >> 16) * amount));
            const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) * amount));
            const b = Math.max(0, Math.min(255, (num & 0x0000FF) * amount));
            return `rgb(${r},${g},${b})`;
        }
        
        function getWallColor(value) {
            switch(value) {
                case 1: return '#808080'; // Normal wall
                case 2: return '#FFD700'; // Repository door
                default: return '#808080';
            }
        }
        
        function render() {
            // Clear and draw ceiling/floor
            ctx.fillStyle = '#2C3E50';
            ctx.fillRect(0, 0, WIDTH, HEIGHT / 2);
            ctx.fillStyle = '#34495E';
            ctx.fillRect(0, HEIGHT / 2, WIDTH, HEIGHT / 2);
            
            // Cast rays
            for (let i = 0; i < NUM_RAYS; i++) {
                const rayAngle = player.angle - HALF_FOV + (i * DELTA_ANGLE);
                const { depth, hitValue } = castRay(rayAngle);
                
                // Fix fish-eye effect
                const distance = depth * Math.cos(rayAngle - player.angle);
                const wallHeight = (TILE_SIZE * HEIGHT) / (distance + 0.0001);
                
                // Calculate shading based on distance
                const shade = Math.max(0.3, 1 - distance / MAX_DEPTH);
                
                const color = getWallColor(hitValue);
                drawWall(i * (WIDTH / NUM_RAYS), wallHeight, color, shade, hitValue);
            }
            
            // Show door text if looking at repository door
            if (lookingAtDoor && currentDoorInfo) {
                doorDescription.innerHTML = `<strong>${currentDoorInfo.repoInfo.title}</strong><br>${currentDoorInfo.repoInfo.description}`;
                doorText.classList.add('show');
            } else {
                doorText.classList.remove('show');
            }
        }
        
        function drawMinimap() {
            const scale = minimap.width / (MAP_SIZE * TILE_SIZE);
            mmCtx.fillStyle = '#000';
            mmCtx.fillRect(0, 0, minimap.width, minimap.height);
            
            // Draw map
            for (let y = 0; y < MAP_SIZE; y++) {
                for (let x = 0; x < MAP_SIZE; x++) {
                    const val = map[y][x];
                    if (val === 1) mmCtx.fillStyle = '#fff';
                    else if (val === 2) mmCtx.fillStyle = '#ff0';
                    else mmCtx.fillStyle = '#222';
                    
                    mmCtx.fillRect(x * TILE_SIZE * scale, y * TILE_SIZE * scale, 
                                   TILE_SIZE * scale, TILE_SIZE * scale);
                }
            }
            
            // Draw player
            mmCtx.fillStyle = '#f00';
            mmCtx.beginPath();
            mmCtx.arc(player.x * scale, player.y * scale, 3, 0, Math.PI * 2);
            mmCtx.fill();
            
            // Draw direction
            mmCtx.strokeStyle = '#f00';
            mmCtx.beginPath();
            mmCtx.moveTo(player.x * scale, player.y * scale);
            mmCtx.lineTo(
                player.x * scale + Math.cos(player.angle) * 15,
                player.y * scale + Math.sin(player.angle) * 15
            );
            mmCtx.stroke();
        }
        
        function update(deltaTime) {
            const moveSpeed = player.speed;
            
            // Movement
            if (keys['w'] || keys['ArrowUp']) {
                const newX = player.x + Math.cos(player.angle) * moveSpeed;
                const newY = player.y + Math.sin(player.angle) * moveSpeed;
                if (!checkCollision(newX, newY)) {
                    player.x = newX;
                    player.y = newY;
                }
            }
            if (keys['s'] || keys['ArrowDown']) {
                const newX = player.x - Math.cos(player.angle) * moveSpeed;
                const newY = player.y - Math.sin(player.angle) * moveSpeed;
                if (!checkCollision(newX, newY)) {
                    player.x = newX;
                    player.y = newY;
                }
            }
            
            // Rotation
            if (keys['a'] || keys['ArrowLeft']) {
                player.angle -= player.rotSpeed;
            }
            if (keys['d'] || keys['ArrowRight']) {
                player.angle += player.rotSpeed;
            }
            
            // Check if looking at door
            const now = Date.now();
            if (now - lastDoorCheck > 100) {
                const doorCheck = checkLookingAtDoor();
                lookingAtDoor = doorCheck.isDoor;
                currentDoorInfo = doorCheck.isDoor ? doorCheck : null;
                lastDoorCheck = now;
            }
            
            // Interaction
            if (keys['e']) {
                interact();
                keys['e'] = false; // Prevent repeated triggers
            }
            
            // Update HUD
            document.getElementById('pos').textContent = 
                `${Math.floor(player.x / TILE_SIZE)}, ${Math.floor(player.y / TILE_SIZE)}`;
        }
        
        function gameLoop(timestamp) {
            if (readmeOpen) {
                requestAnimationFrame(gameLoop);
                return;
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
            
            update(deltaTime);
            render();
            drawMinimap();
            
            requestAnimationFrame(gameLoop);
        }
        
        // Event listeners
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && readmeOpen) {
                closeReadme();
            }
            keys[e.key.toLowerCase()] = true;
        });
        
        window.addEventListener('keyup', (e) => {
            keys[e.key.toLowerCase()] = false;
        });
        
        // Start game
        requestAnimationFrame(gameLoop);

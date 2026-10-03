# Asteroid Game

Pilot your ship through an asteroid field while an enemy ship searches for you. Destroy asteroids, avoid collisions, and score 20 points to win.

## Controls

| Action | Control |
| --- | --- |
| Turn left | Left Arrow or `A` |
| Turn right | Right Arrow or `D` |
| Thrust forward | Up Arrow or `W` |
| Fire | Left mouse button |
| Change enemy field of view | `1`, `2`, `3`, or `4` |
| Restart after the game ends | `R` |

The ship wraps around the edges of the screen. Click the game area first if keyboard controls do not respond in your browser.

## How to Play

- Destroy asteroids to earn points. Reach 20 points to win.
- Avoid asteroids and the enemy's missiles; either can end the game.
- The enemy is frozen for the first five seconds, then patrols and chases when it detects you.
- Use `1` through `4` to change how directly the enemy must be facing you to detect you. Higher numbers make its field-of-view threshold stricter.
- You are briefly invulnerable after starting or restarting.

## Run on Your Computer

Requires Python and Pygame. From the project folder, run:

```powershell
py -m pip install pygame
py main.py
```

## Play in a Browser

After GitHub Pages is enabled and the deployment workflow succeeds, the game will be available at:

https://sleepyjonahhh.github.io/Lab-2-5-Asteroid-Game/

The workflow builds the browser version with Pygbag whenever changes are pushed to `main`.
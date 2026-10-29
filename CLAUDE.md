# TheBlackHole — guia rápido para o Claude

Simulação 3D com renderer próprio (pygame-ce + NumPy). Plano diário em `ROADMAP.md` (1 tarefa/dia, ≤45 min).

## Estrutura (`src/theblackhole/`)
| Ficheiro | Conteúdo |
|---|---|
| `config.py` | Todas as constantes (ecrã, câmara, planeta, jogador, cores) |
| `camera.py` | `normalize`, `Camera` (look_at, set_yaw_pitch, project) |
| `render.py` | `clip_polygon_near`, `draw_faces` (painter's), `shade_color` |
| `star.py` / `sun.py` / `starfield.py` | `Star3D`, `Sun3D`, `StarField3D` |
| `planet.py` | `Planet` (cube-sphere, LOD near/far) |
| `player.py` | `Player` (astronauta em caixas, andar numa esfera) |
| `physics.py` | `Body`, `GravitySystem` (gravidade N-corpos vetorizada em NumPy, Velocity Verlet, energia e momento) |
| `solar_system.py` | `SolarSystem`, `OrbitingPlanet` (planetas em órbita do Sol, rastos) |
| `timecontrol.py` | `TimeControl` (pausa e velocidade da simulação) |
| `blackhole.py` | `schwarzschild_radius`, `BlackHole` (horizonte, sombra), `BlackHoleScene` (cena da tecla B) |
| `main.py` | `SpaceSimulation3D` (loop, input, câmara 3.ª pessoa/livre, HUD) + `main()` |

`space_simulation.py` na raiz = versão 2D antiga (não mexer).

## Correr / verificar
- Python com dependências: `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` (`py` não tem pygame).
- Jogo: `cd src && <python> -m theblackhole`.
- Testes: `<python> -m pytest -q` (na raiz; `pythonpath = src` no `pyproject.toml`).
- Profiling sem janela: `<python> scripts/profile_frames.py [frames]` (ms por frame em cada modo + top 15 do cProfile).
- Teste rápido sem janela (Git Bash), a partir de `src/`:
  `SDL_VIDEODRIVER=dummy <python> -c "import pygame,theblackhole.main as m;pygame.init();s=m.SpaceSimulation3D();[ (s.update(1/60),s.draw()) for _ in range(30)];s.toggle_mode();[(s.update(1/60),s.draw()) for _ in range(30)];print('ok')"`

## Fluxo de cada dia
1. Ler o próximo dia em `ROADMAP.md`; propor o plano em poucas linhas; esperar OK.
2. Implementar; correr o teste rápido.
3. Marcar `[x]`, linha no diário do `ROADMAP.md`, 1–3 commits (`feat:`/`fix:`/`refactor:`/`test:`/`docs:`), sem push.
4. Atualizar a nota do vault `Projetos/TheBlackHole.md` e o diário do vault.

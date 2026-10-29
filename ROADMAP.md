# 🕳️ TheBlackHole — Roadmap

Plano de trabalho diário. **Uma tarefa por dia.** Marca `[x]` quando terminares.

## ⏱️ Limite diário

- **Máximo 45 minutos** por dia (mínimo 15 nos dias difíceis).
- **1 tarefa** da lista. Se acabares mais cedo, paras. Não se adianta trabalho.
- **1 a 3 commits** com mensagens claras (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- O código tem de **correr** no fim da sessão. Nada fica partido no `main`.
- Dia falhado não se compensa com dois no dia seguinte. Continua-se do ponto onde ficou.

---

## Fase 1 — Limpeza e fundações (dias 1–7)

- [x] **Dia 1** — Escolher uma versão 3D (a `_fixed` está limpa; a `space_simulation_3d.py` tem classes duplicadas), apagar a outra e atualizar o README
- [x] **Dia 2** — Adicionar `.gitignore`, `LICENSE` (MIT) e atualizar o `requirements.txt` para versões recentes
- [x] **Dia 3** — Reorganizar em pacote: `src/theblackhole/` com `star.py`, `sun.py`, `starfield.py`, `main.py`
- [x] **Dia 4** — Extrair uma classe `Camera` (posição, pitch, yaw, `project()`) e remover a lógica repetida nas estrelas *(feito no dia 2, junto com o planeta)*
- [x] **Dia 5** — Criar `config.py` com todas as constantes (ecrã, cores, velocidades)
- [x] **Dia 6** — Primeiros testes com `pytest` (projeção 3D→2D, rotação da câmara)
- [x] **Dia 7** — GitHub Actions: CI com `ruff` + `pytest` a cada push

## Fase 2 — Física a sério (dias 8–14)

- [x] **Dia 8** — Motor de gravidade com integrador Velocity Verlet
- [x] **Dia 9** — Planetas em órbita do Sol
- [x] **Dia 10** — Rastos das órbitas (trails)
- [x] **Dia 11** — Controlo do tempo: pausa, acelerar e abrandar (`P`, `+`, `-`)
- [x] **Dia 12** — Teste de conservação de energia (prova que a física está certa)
- [x] **Dia 13** — Vetorizar a física com NumPy (performance)
- [x] **Dia 14** — Mostrar FPS, fazer profiling e otimizar o render

## Fase 3 — O buraco negro (dias 15–21)

- [x] **Dia 15** — Classe `BlackHole` com horizonte de eventos (raio de Schwarzschild)
- [ ] **Dia 16** — Disco de acreção feito de partículas em rotação
- [ ] **Dia 17** — Objetos capturados: tudo o que cruza o horizonte desaparece
- [ ] **Dia 18** — Lente gravitacional aproximada (desviar a luz das estrelas de fundo)
- [ ] **Dia 19** — Efeitos de brilho e glow
- [ ] **Dia 20** — HUD com massa, distância ao buraco negro e velocidade
- [ ] **Dia 21** — Menu inicial com cenários (Sistema Solar, Buraco Negro, Galáxia)

## Fase 4 — Portefólio (dias 22–28)

- [ ] **Dia 22** — Screenshots e GIF animado no README
- [ ] **Dia 23** — Type hints e docstrings em todo o código
- [ ] **Dia 24** — Guardar e carregar cenários em JSON
- [ ] **Dia 25** — Badges no README (CI, Python, licença)
- [ ] **Dia 26** — Executável com PyInstaller
- [ ] **Dia 27** — Release `v1.0.0` no GitHub com tag e changelog
- [ ] **Dia 28** — Texto do projeto para o CV/LinkedIn e um post a mostrar o resultado

---

## 📓 Diário

| Dia | Data | O que fiz |
|-----|------|-----------|
| 1 | 2026-10-09 | Removida a versão 3D partida (classes duplicadas); a versão limpa passou a `space_simulation_3d.py`; README atualizado |
| 2 | 2026-10-12 | **Extra:** planeta esférico com jogador em 3ª pessoa (andar, correr, saltar), dia/noite, câmara livre com TAB; classe `Camera` (Dia 4) |
| 2 | 2026-10-12 | `.gitignore` e `LICENSE` (MIT); `requirements.txt` passou para `pygame-ce==2.5.8` (o fork que já estava em uso) e `numpy==2.3.1` |
| 3 | 2026-10-14 | Código dividido no pacote `src/theblackhole/` (config, camera, render, star, sun, starfield, planet, player, main); `pyproject.toml` com o comando `theblackhole`; README atualizado |
| 5 | 2026-10-15 | Valores de afinação (estrelas, câmaras, LOD e cores do planeta, fato, HUD, dt máximo) passados para `config.py` |
| 6 | 2026-10-29 | `pytest` com 13 testes da `Camera` em `tests/test_camera.py` (centro do ecrã, eixos, distância, plano near, single vs batch, yaw/pitch, `look_at`, base ortonormal); config em `pyproject.toml` |
| 7 | 2026-10-29 | **Extra (pedido do Francisco, mesmo dia do Dia 6):** CI no GitHub Actions (`ruff` 0.17.3 fixo + `pytest`, Python 3.12) a cada push e PR; config do `ruff` no `pyproject.toml` (exclui a versão 2D antiga); 3 avisos corrigidos; badge no README |
| 8 | 2026-10-29 | **Extra (mesmo dia):** `physics.py` com `Body` e `GravitySystem` (gravidade N-corpos com softening, integrador Velocity Verlet kick-drift-kick); constantes em `config.py`; 4 testes (linha reta, 3.ª lei de Newton, momento conservado, órbita circular fecha num período). Ainda não está ligado ao render (Dia 9) |
| 9 | 2026-10-29 | **Extra (mesmo dia):** `solar_system.py`: 4 planetas em órbita circular do Sol (`SolarSystem` sobre o `GravitySystem`, subpassos de 1/120 s), desenhados como esferas com fase de iluminação e ordenados em profundidade com o planeta do jogador; 2 testes |
| 10 | 2026-10-29 | **Extra (mesmo dia):** rastos das órbitas: cada planeta guarda 240 posições (uma a cada 0,1 s) num `deque` e desenha uma linha que se desvanece até ao ponto mais antigo; 1 teste |
| 11 | 2026-10-29 | **Extra (mesmo dia):** controlo do tempo (`timecontrol.py`): `P` pausa as órbitas, `+`/`-` dobram ou dividem a velocidade (x1/8 a x64); o jogador continua em tempo real; HUD mostra a velocidade; 3 testes |
| 12 | 2026-10-29 | **Extra (mesmo dia):** `GravitySystem.total_energy()` (cinética + potencial com softening); teste com órbita excêntrica (e = 0,6) durante ~10 voltas: erro máximo 2,5e-5 com Verlet contra 28 % com Euler explícito (2.º teste mostra a diferença) |
| 13 | 2026-10-29 | **Extra (mesmo dia):** física vetorizada: estado em arrays (N, 3) com os `Body` como vistas; acelerações e energia com `einsum` em vez do ciclo par a par. 100 corpos: 30,8 → 0,52 ms por passo (~60x); 400 corpos: 7 ms. Teste novo compara com a fórmula par a par |
| 14 | 2026-10-29 | **Extra (mesmo dia):** FPS já estava no HUD; `scripts/profile_frames.py` (cProfile sem janela). Gargalo: faces cortadas no plano near projetadas com dezenas de milhares de píxeis (90 % do tempo no `pygame.draw.polygon`). Recorte Sutherland-Hodgman ao ecrã (`fill_polygon`): planeta 19,5 → 10,4 ms/frame, câmara livre 28,1 → 12,3 ms; 4 testes |
| 15 | 2026-10-29 | **Extra (mesmo dia):** `blackhole.py`: `BlackHole` (`Body`) com raio de Schwarzschild r_s = 2GM/c² (c em unidades da cena → r_s ≈ 40) e sombra de 2,6 r_s com anel de fotões; `BlackHoleScene` com estrelas sem Sol; tecla `B` alterna entre o Sistema Solar e o buraco negro; 2 testes |

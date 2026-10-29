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
- [x] **Dia 16** — Disco de acreção feito de partículas em rotação
- [x] **Dia 17** — Objetos capturados: tudo o que cruza o horizonte desaparece
- [x] **Dia 18** — Lente gravitacional aproximada (desviar a luz das estrelas de fundo)
- [x] **Dia 19** — Efeitos de brilho e glow
- [x] **Dia 20** — HUD com massa, distância ao buraco negro e velocidade
- [x] **Dia 21** — Menu inicial com cenários (Sistema Solar, Buraco Negro, Galáxia)

## Fase 4 — Portefólio (dias 22–28)

- [x] **Dia 22** — Screenshots e GIF animado no README
- [x] **Dia 23** — Type hints e docstrings em todo o código
- [x] **Dia 24** — Guardar e carregar cenários em JSON
- [x] **Dia 25** — Badges no README (CI, Python, licença)
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
| 16 | 2026-10-29 | **Extra (mesmo dia):** `AccretionDisk`: 1500 partículas sem massa em órbita circular entre 3 e 10 r_s, integradas em arrays NumPy (Verlet) só com a gravidade do buraco negro; cor do branco quente (interior) ao vermelho (exterior); desenhadas atrás/à frente do buraco por profundidade (~4,7 ms/frame); 1 teste |
| 17 | 2026-10-29 | **Extra (mesmo dia):** captura: o disco perde 1 % da velocidade por segundo e cai em espiral (~1 min desde 3 r_s); partículas que cruzam r_s contam como capturadas e renascem fora; tecla `F` atira rochas (`Rock` no `GravitySystem`, com `add`/`remove`) que desaparecem no horizonte; contador "Captured" no HUD; 3 testes |
| 18 | 2026-10-29 | **Extra (mesmo dia):** lente gravitacional (lente pontual em espaço de ecrã): raio de Einstein θ_E = sqrt(2 r_s · D_ls / (D_l · D_s)); cada estrela atrás do buraco passa a 2 imagens θ = (β ± sqrt(β² + 4θ_E²))/2 e as que caem dentro da sombra desaparecem; `Star.draw` aceita um `lens`; 1800 estrelas de fundo na cena; 3 testes da equação da lente |
| 19 | 2026-10-29 | **Extra (mesmo dia):** `glow.py`: sprites de brilho radial (queda quadrática, em cache) desenhados com `BLEND_ADD`, por isso somam onde se sobrepõem; aplicados às partículas do disco (o interior quente fica a brilhar), ao anel de fotões e ao Sol; ~15,7 ms/frame na cena do buraco negro; 2 testes |
| 20 | 2026-10-29 | **Extra (mesmo dia):** HUD do buraco negro (`hud_readout`): massa, r_s, distância (unidades e em r_s), velocidade da câmara (e em c), velocidade de escape no local e ritmo do relógio sqrt(1 - r_s/r); corrigido bug de aliasing da `Camera` (guardava o array da câmara livre sem copiar); 3 testes |
| 21 | 2026-10-29 | **Extra (mesmo dia):** menu inicial (setas + Enter ou 1-3; ESC numa cena volta ao menu, ESC no menu sai); cenário novo `galaxy.py`: 3000 estrelas em 2 braços em espiral logarítmica com curva de rotação plana (halo de matéria escura), por isso os braços enrolam-se com o tempo, bojo com brilho e buraco negro central; a tecla `B` saiu (o menu substitui-a); 3 testes |
| 22 | 2026-10-29 | **Extra (mesmo dia):** `scripts/capture.py` gera sem janela 5 screenshots e um GIF (72 frames, a câmara à volta do buraco negro, 1,9 MB) em `docs/images/`; README reescrito com os 3 cenários, física, controlos, desenvolvimento e unidades; Pillow nas dependências de dev |
| 23 | 2026-10-29 | **Extra (mesmo dia):** type hints em todas as funções e docstrings em todas as classes e métodos públicos de `src/` (inseridos com um script `ast` e revistos com o `mypy`: 91 → 20 avisos, os restantes são dtypes do NumPy); `aliases.py` com `Vector`, `Color`, `Point2`, `Lens`; o ruff passa a exigir `ANN` e `D10x` no pacote; `sun_position` passou para dentro do `StarField3D` |
| 24 | 2026-10-29 | **Extra (mesmo dia):** `scenario.py` + `to_dict`/`from_dict` no Sistema Solar, buraco negro (rochas e capturas; o disco é regenerado) e galáxia; `F5` guarda e `F9` carrega `saves/<cenário>.json` com mensagem no ecrã; todos os valores lidos são validados (números finitos, massas positivas, vetores de 3) e um ficheiro mau não estraga a cena em curso; 11 testes |
| 25 | 2026-10-29 | **Extra (mesmo dia):** badges no README (CI, Python 3.11+, licença MIT, ruff); corrigido o mínimo de Python para 3.11 (o `numpy==2.3.1` fixado não instala em 3.10) e a CI passou a testar 3.11, 3.12 e 3.13 para o badge ser verdade |

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
- [ ] **Dia 2** — Adicionar `.gitignore`, `LICENSE` (MIT) e atualizar o `requirements.txt` para versões recentes
- [ ] **Dia 3** — Reorganizar em pacote: `src/theblackhole/` com `star.py`, `sun.py`, `starfield.py`, `main.py`
- [ ] **Dia 4** — Extrair uma classe `Camera` (posição, pitch, yaw, `project()`) e remover a lógica repetida nas estrelas
- [ ] **Dia 5** — Criar `config.py` com todas as constantes (ecrã, cores, velocidades)
- [ ] **Dia 6** — Primeiros testes com `pytest` (projeção 3D→2D, rotação da câmara)
- [ ] **Dia 7** — GitHub Actions: CI com `ruff` + `pytest` a cada push

## Fase 2 — Física a sério (dias 8–14)

- [ ] **Dia 8** — Motor de gravidade com integrador Velocity Verlet
- [ ] **Dia 9** — Planetas em órbita do Sol
- [ ] **Dia 10** — Rastos das órbitas (trails)
- [ ] **Dia 11** — Controlo do tempo: pausa, acelerar e abrandar (`P`, `+`, `-`)
- [ ] **Dia 12** — Teste de conservação de energia (prova que a física está certa)
- [ ] **Dia 13** — Vetorizar a física com NumPy (performance)
- [ ] **Dia 14** — Mostrar FPS, fazer profiling e otimizar o render

## Fase 3 — O buraco negro (dias 15–21)

- [ ] **Dia 15** — Classe `BlackHole` com horizonte de eventos (raio de Schwarzschild)
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

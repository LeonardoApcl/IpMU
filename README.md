# IpMU — VNS (BVNS/RVNS) em C++

Heurística baseada em **Variable Neighborhood Search** para o *Induced p-Median
Problem with Upgrades* (IpMU), baseada no artigo de Salazar et al.,
*Knowledge-Based Systems* 339 (2026). O núcleo de otimização é em C++; a
visualização é em Python.

## Modelo (fiel ao artigo)

- Grafo dirigido com dois pesos por aresta: **tempo** `c1` e **custo** `c2`; cada
  nó tem uma **demanda**.
- Selecionar `p` medianas. Cada cliente é servido pela mediana de **menor tempo**
  (empate → menor custo). O custo do objetivo é o `c2` somado ao longo desse
  caminho, ponderado pela demanda.
- Orçamento `B` reduz o `c2` de arestas atualizáveis (subproblema de upgrade resolvido por guloso, `relax_edges`). Aqui o upgrade pode
  reduzir o custo **até 0**, limitado apenas por `B`.

Como upgrades só mexem no custo, os caminhos mais rápidos (por tempo) são fixos
após escolher as medianas, por isso usamos **um Floyd-Warshall lexicográfico**
no par `(tempo, custo)` (e não um FW independente de custo).

## Estrutura

```
src/
  core/         instance (parser), problem (FW lexicográfico), solution (avaliação), upgrade (relax_edges)
  construction/ grasp_construction (α-RCL)
  localsearch/  swap_local_search (1-troca, melhor-melhora)
  shaking/      shaking.hpp + random_swap / greedy   (estratégias plugáveis)
  metaheuristics/ vns.hpp + bvns / rvns               (algoritmos plugáveis)
  util/         rng, json_writer
  main.cpp      CLI
python/
  visualizacao.py    desenho do grafo/solução
  plot_solution.py   ponte: lê instância + JSON do C++ e desenha
instances/      instâncias no formato do benchmark
```

## Formato da instância

```
linha 1: n            (nº de nós)
linha 2: d            (nº de arestas atualizáveis; informativo)
linha 3: p            (nº de medianas)
linha 4: B            (orçamento)
arestas: i j flag c1 c2   (1-indexado; flag=atualizável; c1=tempo; c2=custo)
linha final: d_1 ... d_n   (demanda de cada nó)
```
O parser deriva o nº de arestas dos tokens, aceitando grafos completos (benchmark)
ou esparsos (ex.: a Fig.1 do artigo).

## Build

```powershell
.\build.ps1            # usa o g++ do MSYS2 (C:\msys64\mingw64), linkagem estática
```
Alternativa com CMake: `cmake -S . -B build && cmake --build build`.

## Execução

```powershell
.\ipmu.exe instances\AUpdata_ta_cp_20_100_2_50_1.txt --alg bvns --out solucao.json
.\.venv\Scripts\python.exe python\plot_solution.py instances\AUpdata_ta_cp_20_100_2_50_1.txt solucao.json
```

Opções do CLI:

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--alg <bvns\|rvns>` | bvns | metaheurística |
| `--shake <random\|greedy>` | random | estratégia de shaking |
| `--alpha <A>` | 0.51 | voracidade da construção GRASP |
| `--kmax <K>` | p | máx. de trocas no shaking |
| `--iters <N>` | 100 | máx. de iterações |
| `--no-improve <N>` | 29 | máx. de iterações sem melhora |
| `--seed <S>` | 42 | semente do RNG (reprodutibilidade) |
| `--out <arq.json>` | — | grava a solução para a visualização |

Trocar de algoritmo (`--alg`) ou de shaking (`--shake`) não exige recompilar —
ambos são intercambiáveis por design, para facilitar comparações experimentais.

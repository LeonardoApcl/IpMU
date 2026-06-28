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
- Orçamento `B` reduz o `c2` de arestas atualizáveis (subproblema de upgrade resolvido por guloso, `relax_edges`). Cada aresta
  pode ser reduzida até o teto `u_a = u_factor·c²` (padrão `0.5`, ajustável por
  `--ucap`), limitado pelo orçamento `B`.

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
arestas: i j flag c1 c2   (1-indexado; flag=presença do arco em A; c1=tempo; c2=custo)
linha final: d_1 ... d_n   (demanda de cada nó)
```
`flag=1` marca um arco do grafo `A` (esparso, |A|=m); linhas `flag=0` **não** são
arcos e são descartadas no parse. O parser deriva o nº de linhas dos tokens, aceitando
tanto os arquivos densos do benchmark (maioria `flag=0`) quanto os esparsos
(ex.: a Fig.1 do artigo, todos `flag=1`).

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
| `--ucap <fator>` | 0.5 | teto do upgrade `u_a = fator·c²` (Fig.1 do artigo: `1.0`) |
| `--out <arq.json>` | — | grava a solução para a visualização |

Trocar de algoritmo (`--alg`) ou de shaking (`--shake`) não exige recompilar —
ambos são intercambiáveis por design, para facilitar comparações experimentais.

## Instâncias e resultados

- `instances/P/` e `instances/R/` (n=20..80) são **versionadas** — o benchmark base
  reproduz direto do clone.
- `instances/BigInstances100200/` (n=100) e `instances/BigInstances500/` (n=500) **não**
  são versionadas (tamanho). Vêm do material suplementar do artigo; coloque-as
  localmente nesses caminhos para rodá-las.
- `results/ResultsInstanceByInstance.xlsx` são os resultados de referência do artigo
  (abas por `n`, com a coluna `SOTA` usada na comparação).

## Reproduzir o benchmark

`python/run_benchmark.py` resolve cada instância com o `ipmu.exe`, grava o progresso
num checkpoint CSV (`results/raw/<alg>_seed<seed>.csv`, append-only com flush por
instância) e gera uma tabela por grupo `n` em `results/report/`, com `Dev` e `isBest?`
calculados contra a coluna `SOTA` do `.xlsx`.

É **pausável e retomável**: pode ser parado a qualquer momento (Ctrl+C) sem perder o
que já terminou; basta re-executar para continuar de onde parou.

```powershell
.\build.ps1
# roda tudo (padrão: instances/, recursivo):
.\.venv\Scripts\python.exe python\run_benchmark.py --alg bvns
# parar com Ctrl+C e depois continuar — re-execute o mesmo comando:
.\.venv\Scripts\python.exe python\run_benchmark.py --alg bvns
# regenerar só a tabela (a partir do checkpoint, mesmo parcial):
.\.venv\Scripts\python.exe python\run_benchmark.py --alg bvns --report-only
# subconjunto específico:
.\.venv\Scripts\python.exe python\run_benchmark.py --instances instances\P\n=20 --alg bvns
```

O runner aceita os mesmos parâmetros do solver (`--shake --alpha --kmax --iters
--no-improve --seed`), repassados a cada execução.

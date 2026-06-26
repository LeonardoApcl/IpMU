import numpy as np
import random
from construcao import construcao_grasp_ipmu
from visualizacao import desenhar_grafo_inicial, desenhar_solucao

if __name__ == "__main__":
    # Exemplo
    num_clientes = 5
    p = 2
    alpha = 0 # puro guloso
    orcamento = 2

    inf = float('inf')
    matriz_tempo = np.full((num_clientes, num_clientes), inf)
    matriz_custo = np.full((num_clientes, num_clientes), inf)

    for i in range(num_clientes):
        matriz_tempo[i][i] = 0
        matriz_custo[i][i] = 0

    # Arestas baseadas na Figura 1 (A=0, B=1, C=2, D=3, E=4)
    # Formato: (Origem, Destino, Tempo(c1), Custo(c2))
    arestas = [
        (0, 1, 1, 4), (0, 2, 4, 7), (0, 4, 8, 3),
        (1, 2, 2, 3),
        (2, 0, 6, 9),
        (3, 2, 5, 6),
        (4, 0, 3, 9), (4, 2, 5, 1), (4, 3, 8, 2)
    ]

    for o, d, t, c in arestas:
        matriz_tempo[o][d] = t
        matriz_custo[o][d] = c

    # Floyd-Warshall nas 2 matrizes

    dist_tempo = matriz_tempo.copy()
    dist_custo = matriz_custo.copy()
    pred_tempo = np.full((num_clientes, num_clientes), -1, dtype=int)

    for i in range(num_clientes):
        for j in range(num_clientes):
            if i != j and matriz_tempo[i][j] < inf:
                pred_tempo[i][j] = j

    for k in range(num_clientes):
        for i in range(num_clientes):
            for j in range(num_clientes):
                if dist_tempo[i][k] + dist_tempo[k][j] < dist_tempo[i][j]:
                    dist_tempo[i][j] = dist_tempo[i][k] + dist_tempo[k][j]
                    pred_tempo[i][j] = pred_tempo[i][k]

    # Forçamos uma seed para evitar flutuações nas primeiras rodadas gulosas caso dê empate
    random.seed(42)

    S, arestas_ativas, arestas_melhoradas = construcao_grasp_ipmu(
        dist_tempo, matriz_custo, pred_tempo, num_clientes, p, alpha, orcamento
    )

    mapa_letras = {0:'A', 1:'B', 2:'C', 3:'D', 4:'E'}
    print(f"Medianas escolhidas: {[mapa_letras[i] for i in S]}")

    print("Rotas ativas (Origem -> Destino): ", end="")
    print([f"{mapa_letras[u]}->{mapa_letras[v]}" for u, v in arestas_ativas])

    print("Arestas com Upgrade Aplicado: ", end="")
    print({f"{mapa_letras[u]}->{mapa_letras[v]}": f"Novo custo: {custo}" for (u, v), custo in arestas_melhoradas.items()})

    desenhar_grafo_inicial(matriz_custo, num_clientes)
    desenhar_solucao(matriz_custo, num_clientes, S, arestas_ativas, arestas_melhoradas)
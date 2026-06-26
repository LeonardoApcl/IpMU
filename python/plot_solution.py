"""Ponte de visualização: lê uma instância do IpMU e o JSON de solução gerado
pelo executável C++ e desenha a solução reusando visualizacao.desenhar_solucao.

Uso:
    python python/plot_solution.py <instancia.txt> <solucao.json>

Toda a lógica de otimização vive no C++; aqui só montamos a matriz de custo a
partir da instância (mesmo formato do benchmark) e repassamos para o desenho.
Nós são tratados 0-indexados, consistente com o JSON do C++.
"""
import json
import math
import sys

from visualizacao import desenhar_solucao


def ler_instancia(caminho):
    """Lê o formato do benchmark e devolve (n, matriz_custo) 0-indexada."""
    with open(caminho, "r", encoding="utf-8") as f:
        tokens = f.read().split()

    pos = 0

    def proximo():
        nonlocal pos
        val = tokens[pos]
        pos += 1
        return val

    n = int(proximo())
    _d = int(proximo())      # nº de arestas atualizáveis (não usado no desenho)
    _p = int(proximo())      # nº de medianas
    _B = float(proximo())    # orçamento

    inf = float("inf")
    matriz_custo = [[inf] * n for _ in range(n)]
    for i in range(n):
        matriz_custo[i][i] = 0

    num_arestas = n * (n - 1)
    for _ in range(num_arestas):
        i = int(proximo()) - 1   # 1-indexado -> 0-indexado
        j = int(proximo()) - 1
        _flag = int(proximo())
        _c1 = float(proximo())   # tempo (não usado no desenho de custo)
        c2 = float(proximo())    # custo
        matriz_custo[i][j] = c2

    # A linha final de demandas é ignorada para a visualização.
    return n, matriz_custo


def main():
    if len(sys.argv) != 3:
        print("Uso: python python/plot_solution.py <instancia.txt> <solucao.json>")
        sys.exit(2)

    caminho_instancia, caminho_json = sys.argv[1], sys.argv[2]

    n, matriz_custo = ler_instancia(caminho_instancia)

    with open(caminho_json, "r", encoding="utf-8") as f:
        sol = json.load(f)

    medianas = sol["medians"]
    arestas_ativas = [tuple(e) for e in sol["active_edges"]]
    # arestas_melhoradas: {(u, v): novo_custo}, custo arredondado para o rótulo.
    arestas_melhoradas = {
        (u, v): round(novo_custo, 2) for u, v, novo_custo in sol["upgraded_edges"]
    }

    print(f"Objetivo: {sol['objective']:.4f}  |  medianas: {medianas}")
    desenhar_solucao(matriz_custo, n, medianas, arestas_ativas, arestas_melhoradas)


if __name__ == "__main__":
    main()

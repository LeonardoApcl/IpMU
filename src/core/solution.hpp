#pragma once

#include <tuple>
#include <vector>

#include "core/problem.hpp"

namespace ipmu {

// Uma solução do IpMU é totalmente descrita pelo conjunto de medianas (o
// subproblema de upgrade é resolvido de forma ótima na avaliação). Guardamos o
// valor de objetivo em cache para evitar reavaliações.
struct Solution {
    std::vector<int> medians;   // tamanho p
    double objective = kInf;    // valor da função objetivo (menor é melhor)

    bool operator<(const Solution& other) const { return objective < other.objective; }
};

// Detalhamento de uma solução, para log e visualização.
struct SolutionDetail {
    double objective = kInf;
    std::vector<Edge> active_edges;                          // arestas usadas pelos clientes
    std::vector<std::tuple<int, int, double>> upgraded_edges;  // (u, v, novo_custo)
    std::vector<int> assignment;  // assignment[cliente] = mediana que o serve (tam. n)
};

// Avalia o objetivo de um conjunto de medianas (caminho quente da busca local):
// atribui cada cliente à mediana lexicograficamente mais próxima (tempo, custo),
// soma o custo base e desconta a economia ótima do orçamento (relax_edges).
// Retorna kInf se algum cliente ficar inalcançável.
double evaluate(const Problem& prob, const std::vector<int>& medians);

// Como evaluate(), mas também coleta arestas ativas e melhoradas para visualização.
SolutionDetail evaluate_detailed(const Problem& prob, const std::vector<int>& medians);

}  // namespace ipmu

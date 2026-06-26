#pragma once

#include <tuple>
#include <vector>

#include "core/problem.hpp"

namespace ipmu {

// Uma aresta ativa e atualizável, candidata a receber orçamento.
//   weight = W(a) = soma das demandas dos clientes cujo caminho passa por 'a'
//   cost   = custo c2 atual da aresta (teto de redução: pode ir até 0)
struct UpgradeItem {
    Edge edge;
    double weight;
    double cost;
};

// Resolve o subproblema de upgrade (Algoritmo 1, "relaxEdges", do artigo):
// um Knapsack Fracionário resolvido por guloso. Ordena as arestas por benefício
// por unidade (weight) e gasta o orçamento reduzindo cada custo em
// x_a = min(cost_a, orçamento_restante), até 0.
//
// Retorna a economia total = Σ x_a · W(a). Se 'upgraded' != nullptr, registra
// nele (u, v, novo_custo) das arestas efetivamente reduzidas (para visualização).
// 'items' é reordenado in-place.
double relax_edges(std::vector<UpgradeItem>& items, double budget,
                   std::vector<std::tuple<int, int, double>>* upgraded = nullptr);

}  // namespace ipmu

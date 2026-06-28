#pragma once

#include <utility>
#include <vector>

#include "core/instance.hpp"

namespace ipmu {

// Aresta dirigida (origem, destino).
using Edge = std::pair<int, int>;

// Encapsula a instância e os caminhos mais curtos pré-calculados.
//
// Roteamento do IpMU: cada cliente é servido pelo caminho de MENOR TEMPO (c1);
// em empate de tempo, escolhe-se o de MENOR CUSTO (c2). Por isso usamos um único
// Floyd-Warshall LEXICOGRÁFICO no par (tempo, custo) — não um FW independente de
// custo, que acharia o caminho mais barato (incorreto para o problema).
//
// Como upgrades só reduzem c2 (nunca c1), os caminhos mais rápidos são fixos
// depois de escolhidas as medianas; daí o subproblema de upgrade poder ser
// resolvido exatamente por um guloso (ver upgrade.hpp).
class Problem {
public:
    explicit Problem(Instance instance);

    const Instance& instance() const { return inst_; }
    int n() const { return inst_.n; }
    int p() const { return inst_.p; }
    double budget() const { return inst_.budget; }
    double u_factor() const { return inst_.u_factor; }  // teto do upgrade: u_a = u_factor·c²
    double demand(int i) const { return inst_.demand[static_cast<std::size_t>(i)]; }

    // Tempo / custo do caminho lexicograficamente ótimo de 'from' a 'to'.
    double dist_time(int from, int to) const { return dist_time_[idx(from, to)]; }
    double dist_cost(int from, int to) const { return dist_cost_[idx(from, to)]; }
    bool reachable(int from, int to) const { return dist_time_[idx(from, to)] < kInf; }

    // Arestas (u, v) do caminho lexicograficamente ótimo de 'from' a 'to'.
    // Vazio se from == to ou se 'to' for inalcançável.
    std::vector<Edge> path_edges(int from, int to) const;

    // Atalhos para os pesos das arestas (custo c2 e se é atualizável).
    double edge_cost(int u, int v) const { return inst_.cost[idx(u, v)]; }
    bool edge_upgradable(int u, int v) const { return inst_.upgradable[idx(u, v)] != 0; }

private:
    int idx(int i, int j) const { return i * inst_.n + j; }

    Instance inst_;
    std::vector<double> dist_time_;  // n*n
    std::vector<double> dist_cost_;  // n*n (custo ao longo do caminho tempo-ótimo)
    std::vector<int> next_;          // n*n, próximo nó no caminho i->j (-1 se inalcançável)
};

}  // namespace ipmu

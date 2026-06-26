#include "core/solution.hpp"

#include <unordered_map>

#include "core/upgrade.hpp"

namespace ipmu {

namespace {

constexpr double kEps = 1e-9;

// Núcleo da avaliação, compartilhado entre evaluate() e evaluate_detailed().
// Quando 'detail' != nullptr, preenche arestas ativas e melhoradas.
double evaluate_impl(const Problem& prob, const std::vector<int>& medians,
                     SolutionDetail* detail) {
    const int n = prob.n();

    // Acumula W(a) = soma das demandas dos clientes cujo caminho passa por 'a'.
    // Chave da aresta: u * n + v.
    std::unordered_map<long long, double> weight;
    weight.reserve(static_cast<std::size_t>(n) * 2);

    for (int client = 0; client < n; ++client) {
        // Mediana lexicograficamente mais próxima: menor tempo; empate -> menor custo.
        int best = -1;
        double best_t = kInf, best_c = kInf;
        for (int m : medians) {
            const double t = prob.dist_time(m, client);
            if (t >= kInf) continue;
            const double c = prob.dist_cost(m, client);
            if (best == -1 || t < best_t - kEps ||
                (t <= best_t + kEps && c < best_c - kEps)) {
                best = m;
                best_t = t;
                best_c = c;
            }
        }
        if (best == -1) {
            return kInf;  // cliente inalcançável -> solução inviável
        }

        const double d = prob.demand(client);
        for (const Edge& e : prob.path_edges(best, client)) {
            const long long key = static_cast<long long>(e.first) * n + e.second;
            weight[key] += d;
        }
    }

    // Custo base = Σ W(a)·custo(a); coleta itens atualizáveis para o relax.
    double base_cost = 0.0;
    std::vector<UpgradeItem> upgradable_items;
    for (const auto& [key, w] : weight) {
        const int u = static_cast<int>(key / n);
        const int v = static_cast<int>(key % n);
        const double c = prob.edge_cost(u, v);
        base_cost += w * c;
        if (prob.edge_upgradable(u, v) && c > 0.0) {
            upgradable_items.push_back(UpgradeItem{Edge{u, v}, w, c});
        }
    }

    std::vector<std::tuple<int, int, double>>* upgraded_ptr =
        detail != nullptr ? &detail->upgraded_edges : nullptr;
    const double savings = relax_edges(upgradable_items, prob.budget(), upgraded_ptr);
    const double objective = base_cost - savings;

    if (detail != nullptr) {
        detail->objective = objective;
        detail->active_edges.reserve(weight.size());
        for (const auto& [key, w] : weight) {
            (void)w;
            detail->active_edges.emplace_back(static_cast<int>(key / n),
                                              static_cast<int>(key % n));
        }
    }
    return objective;
}

}  // namespace

double evaluate(const Problem& prob, const std::vector<int>& medians) {
    return evaluate_impl(prob, medians, nullptr);
}

SolutionDetail evaluate_detailed(const Problem& prob, const std::vector<int>& medians) {
    SolutionDetail detail;
    evaluate_impl(prob, medians, &detail);
    return detail;
}

}  // namespace ipmu

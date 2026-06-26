#include <algorithm>
#include <vector>

#include "shaking/shaking.hpp"

namespace ipmu {

// Remove k medianas aleatórias e reinsere k não-medianas escolhidas gulosamente
// (a cada passo, o nó que minimiza o objetivo). É um shaking mais "guiado" que o
// aleatório puro: perturba a estrutura mas reconstrói com qualidade.
Solution shake_greedy(const Solution& sol, int k, Rng& rng, const Problem& prob) {
    const int n = prob.n();
    const int p = static_cast<int>(sol.medians.size());
    const int swaps = std::min(k, p);

    std::vector<char> is_median(static_cast<std::size_t>(n), 0);
    for (int m : sol.medians) is_median[static_cast<std::size_t>(m)] = 1;

    // Sorteia 'swaps' posições distintas para remover.
    std::vector<int> positions(static_cast<std::size_t>(p));
    for (int i = 0; i < p; ++i) positions[static_cast<std::size_t>(i)] = i;
    std::shuffle(positions.begin(), positions.end(), rng.engine());

    // Conjunto parcial = medianas sobreviventes.
    Solution result;
    result.medians.reserve(static_cast<std::size_t>(p));
    for (int i = swaps; i < p; ++i) {
        result.medians.push_back(sol.medians[static_cast<std::size_t>(positions[static_cast<std::size_t>(i)])]);
    }
    for (int i = 0; i < swaps; ++i) {
        const int removed = sol.medians[static_cast<std::size_t>(positions[static_cast<std::size_t>(i)])];
        is_median[static_cast<std::size_t>(removed)] = 0;
    }

    // Reinsere gulosamente: a cada passo, a melhor não-mediana (append ao parcial).
    for (int s = 0; s < swaps; ++s) {
        int best_in = -1;
        double best_obj = kInf;
        result.medians.push_back(-1);
        for (int in = 0; in < n; ++in) {
            if (is_median[static_cast<std::size_t>(in)]) continue;
            result.medians.back() = in;
            const double obj = evaluate(prob, result.medians);
            if (obj < best_obj) {
                best_obj = obj;
                best_in = in;
            }
        }
        result.medians.back() = best_in;
        is_median[static_cast<std::size_t>(best_in)] = 1;
    }

    result.objective = evaluate(prob, result.medians);
    return result;
}

}  // namespace ipmu

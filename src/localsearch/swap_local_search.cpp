#include "localsearch/swap_local_search.hpp"

#include <vector>

namespace ipmu {

Solution local_search_swap(const Problem& prob, Solution sol) {
    const int n = prob.n();
    const int p = static_cast<int>(sol.medians.size());

    std::vector<char> is_median(static_cast<std::size_t>(n), 0);
    for (int m : sol.medians) is_median[static_cast<std::size_t>(m)] = 1;

    if (sol.objective >= kInf) {
        sol.objective = evaluate(prob, sol.medians);
    }

    bool improved = true;
    while (improved) {
        improved = false;

        int best_pos = -1;       // posição da mediana a remover
        int best_in = -1;        // nó a inserir
        double best_obj = sol.objective;

        for (int pos = 0; pos < p; ++pos) {
            const int removed = sol.medians[static_cast<std::size_t>(pos)];
            for (int in = 0; in < n; ++in) {
                if (is_median[static_cast<std::size_t>(in)]) continue;

                sol.medians[static_cast<std::size_t>(pos)] = in;
                const double obj = evaluate(prob, sol.medians);
                sol.medians[static_cast<std::size_t>(pos)] = removed;

                if (obj < best_obj) {
                    best_obj = obj;
                    best_pos = pos;
                    best_in = in;
                }
            }
        }

        if (best_pos != -1) {
            const int removed = sol.medians[static_cast<std::size_t>(best_pos)];
            sol.medians[static_cast<std::size_t>(best_pos)] = best_in;
            is_median[static_cast<std::size_t>(removed)] = 0;
            is_median[static_cast<std::size_t>(best_in)] = 1;
            sol.objective = best_obj;
            improved = true;
        }
    }

    return sol;
}

}  // namespace ipmu

#include "construction/grasp_construction.hpp"

#include <algorithm>
#include <vector>

namespace ipmu {

Solution construct_grasp(const Problem& prob, double alpha, Rng& rng) {
    const int n = prob.n();
    const int p = prob.p();

    Solution sol;
    sol.medians.reserve(static_cast<std::size_t>(p));

    std::vector<int> candidates(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) candidates[static_cast<std::size_t>(i)] = i;

    while (static_cast<int>(sol.medians.size()) < p) {
        std::vector<double> cost(candidates.size());
        double c_min = kInf;
        double c_max = -kInf;  // máximo entre os finitos

        for (std::size_t k = 0; k < candidates.size(); ++k) {
            sol.medians.push_back(candidates[k]);
            const double c = evaluate(prob, sol.medians);
            sol.medians.pop_back();
            cost[k] = c;
            if (c < c_min) c_min = c;
            if (c < kInf && c > c_max) c_max = c;
        }

        // Monta a RCL.
        std::vector<int> rcl;
        if (c_min >= kInf) {
            // Nenhum candidato torna a solução viável ainda: RCL = todos.
            rcl = candidates;
        } else {
            const double threshold = c_min + alpha * (c_max - c_min);
            for (std::size_t k = 0; k < candidates.size(); ++k) {
                if (cost[k] <= threshold) {
                    rcl.push_back(candidates[k]);
                }
            }
        }

        const int chosen = rng.choice(rcl);
        sol.medians.push_back(chosen);
        candidates.erase(
            std::find(candidates.begin(), candidates.end(), chosen));
    }

    sol.objective = evaluate(prob, sol.medians);
    return sol;
}

}  // namespace ipmu

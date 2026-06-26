#include <algorithm>
#include <stdexcept>
#include <vector>

#include "shaking/shaking.hpp"

namespace ipmu {

Solution shake_random_swap(const Solution& sol, int k, Rng& rng, const Problem& prob) {
    const int n = prob.n();
    const int p = static_cast<int>(sol.medians.size());

    Solution result = sol;
    std::vector<char> is_median(static_cast<std::size_t>(n), 0);
    for (int m : result.medians) is_median[static_cast<std::size_t>(m)] = 1;

    const int swaps = std::min(k, p);
    for (int s = 0; s < swaps; ++s) {
        // Remove uma mediana aleatória.
        const int pos = rng.next_index(p);
        const int removed = result.medians[static_cast<std::size_t>(pos)];

        // Sorteia um nó não-mediano para entrar.
        int in;
        do {
            in = rng.next_index(n);
        } while (is_median[static_cast<std::size_t>(in)]);

        result.medians[static_cast<std::size_t>(pos)] = in;
        is_median[static_cast<std::size_t>(removed)] = 0;
        is_median[static_cast<std::size_t>(in)] = 1;
    }

    result.objective = evaluate(prob, result.medians);
    return result;
}

ShakeFn make_shaking(const std::string& name) {
    if (name == "random") return shake_random_swap;
    if (name == "greedy") return shake_greedy;
    throw std::runtime_error("estratégia de shaking desconhecida: " + name);
}

}  // namespace ipmu

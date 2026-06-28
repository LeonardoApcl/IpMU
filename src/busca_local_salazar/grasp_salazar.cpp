#include "busca_local_salazar/grasp_salazar.hpp"

#include "construction/grasp_construction.hpp"

namespace ipmu {

namespace {
constexpr double kEps = 1e-9;
}

VnsResult run_grasp(const Problem& prob, const Solution& initial,
                    const VnsParams& params, double alpha,
                    const LocalSearchFn& local_search, Rng& rng) {
    VnsResult result;
    // Iteração 0: ótimo local da construção inicial já feita no main.
    result.best = local_search(prob, initial);

    long iters = 0;
    long no_improve = 0;

    while (iters < params.max_iters && no_improve < params.max_iters_no_improve) {
        ++iters;
        // Reconstrói do zero (diversificação) e refina (intensificação).
        Solution cand = local_search(prob, construct_grasp(prob, alpha, rng));

        if (cand.objective < result.best.objective - kEps) {
            result.best = std::move(cand);
            no_improve = 0;
        } else {
            ++no_improve;
        }
    }

    result.iters = iters;
    result.iters_no_improve = no_improve;
    return result;
}

}  // namespace ipmu

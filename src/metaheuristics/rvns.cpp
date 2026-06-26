#include "metaheuristics/vns.hpp"

namespace ipmu {

namespace {
constexpr double kEps = 1e-9;
}

VnsResult run_rvns(const Problem& prob, const Solution& initial, const VnsParams& params,
                   const ShakeFn& shake, Rng& rng) {
    const int k_max = params.k_max > 0 ? params.k_max : prob.p();

    VnsResult result;
    result.best = initial;
    if (result.best.objective >= kInf) {
        result.best.objective = evaluate(prob, result.best.medians);
    }

    long iters = 0;
    long no_improve = 0;
    int k = 1;

    while (iters < params.max_iters && no_improve < params.max_iters_no_improve) {
        ++iters;
        Solution candidate = shake(result.best, k, rng, prob);  // sem busca local

        if (candidate.objective < result.best.objective - kEps) {
            result.best = std::move(candidate);
            k = 1;
            no_improve = 0;
        } else {
            ++no_improve;
            ++k;
            if (k > k_max) k = 1;
        }
    }

    result.iters = iters;
    result.iters_no_improve = no_improve;
    return result;
}

}  // namespace ipmu

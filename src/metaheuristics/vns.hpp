#pragma once

#include <functional>

#include "core/problem.hpp"
#include "core/solution.hpp"
#include "shaking/shaking.hpp"
#include "util/rng.hpp"

namespace ipmu {

// Busca local plugável (mesma assinatura de local_search_swap, adaptada).
using LocalSearchFn = std::function<Solution(const Problem&, Solution)>;

struct VnsParams {
    int k_max = 0;                    // nº máx. de trocas no shaking; 0 => usa p
    long max_iters = 100;             // nº máx. de iterações (shakes)
    long max_iters_no_improve = 29;   // parada antecipada sem melhora (irace: 29)
};

struct VnsResult {
    Solution best;
    long iters = 0;
    long iters_no_improve = 0;
};

// Basic VNS: shaking em N_k -> busca local -> aceita e reinicia k se melhorar,
// senão k++. Recebe a estratégia de shaking e a busca local por parâmetro, para
// troca trivial nos experimentos.
VnsResult run_bvns(const Problem& prob, const Solution& initial, const VnsParams& params,
                   const ShakeFn& shake, const LocalSearchFn& local_search, Rng& rng);

// Reduced VNS: igual ao BVNS, porém SEM busca local (só shaking + aceitação).
VnsResult run_rvns(const Problem& prob, const Solution& initial, const VnsParams& params,
                   const ShakeFn& shake, Rng& rng);

}  // namespace ipmu

#pragma once

#include "core/problem.hpp"
#include "core/solution.hpp"
#include "metaheuristics/vns.hpp"  // VnsParams, VnsResult, LocalSearchFn
#include "util/rng.hpp"

namespace ipmu {

// GRASP do artigo (Salazar et al.): multi-start construct_grasp + busca local de
// melhor-melhora. Cada iteração reconstrói uma solução do zero (construção
// gulosa-randomizada) e aplica a busca local; guarda a melhor encontrada.
// Parâmetros de parada: VnsParams::max_iters e max_iters_no_improve (mesmos
// valores do VNS para comparação justa: 100 iters, 29 sem melhora).
VnsResult run_grasp(const Problem& prob, const Solution& initial,
                    const VnsParams& params, double alpha,
                    const LocalSearchFn& local_search, Rng& rng);

}  // namespace ipmu

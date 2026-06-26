#pragma once

#include <functional>
#include <string>

#include "core/problem.hpp"
#include "core/solution.hpp"
#include "util/rng.hpp"

namespace ipmu {

// Interface comum de shaking: produz uma solução na vizinhança N_k (k trocas) da
// solução dada. Trocar a estratégia é só trocar a ShakeFn passada ao VNS — por
// isso cada estratégia vive em seu próprio .cpp.
using ShakeFn = std::function<Solution(const Solution&, int k, Rng&, const Problem&)>;

// Estratégia padrão: k trocas puramente aleatórias.
Solution shake_random_swap(const Solution& sol, int k, Rng& rng, const Problem& prob);

// Estratégia enviesada: remove k medianas aleatórias e reinsere gulosamente as
// melhores não-medianas (reconstrução parcial). Para comparação experimental.
Solution shake_greedy(const Solution& sol, int k, Rng& rng, const Problem& prob);

// Fábrica por nome ("random" | "greedy"). Lança std::runtime_error se inválido.
ShakeFn make_shaking(const std::string& name);

}  // namespace ipmu

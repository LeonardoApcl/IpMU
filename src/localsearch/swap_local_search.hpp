#pragma once

#include "core/problem.hpp"
#include "core/solution.hpp"

namespace ipmu {

// Busca local de melhor-melhora na vizinhança de troca (Algoritmo 5 do artigo):
// vizinhança de Hamming 1 = trocar uma mediana por uma não-mediana. A cada passo
// aplica a melhor troca que melhora o objetivo; para num ótimo local.
// Recebe a solução por valor e devolve a versão otimizada.
Solution local_search_swap(const Problem& prob, Solution sol);

}  // namespace ipmu

#pragma once

#include "core/problem.hpp"
#include "core/solution.hpp"
#include "util/rng.hpp"

namespace ipmu {

// Fase de construção do GRASP (Algoritmo 4 do artigo / construcao.py).
// Constrói uma solução adicionando uma mediana por vez: avalia o objetivo ao
// inserir cada candidato, monta a Lista Restrita de Candidatos (RCL) pelo limiar
// c_min + alpha*(c_max - c_min) e sorteia um candidato dela.
//   alpha = 0  -> totalmente guloso;  alpha = 1 -> totalmente aleatório.
Solution construct_grasp(const Problem& prob, double alpha, Rng& rng);

}  // namespace ipmu

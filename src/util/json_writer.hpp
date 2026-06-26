#pragma once

#include <string>
#include <vector>

#include "core/problem.hpp"
#include "core/solution.hpp"

namespace ipmu {

// Serializa a solução em JSON (sem dependências externas) para a ponte de
// visualização em Python. Nós são gravados 0-indexados. Lança em erro de escrita.
void write_solution_json(const std::string& path, const std::string& instance_path,
                         const Problem& prob, const std::vector<int>& medians,
                         const SolutionDetail& detail);

}  // namespace ipmu

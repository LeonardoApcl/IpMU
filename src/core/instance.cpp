#include "core/instance.hpp"

#include <fstream>
#include <stdexcept>
#include <vector>

namespace ipmu {

Instance read_instance(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("não foi possível abrir a instância: " + path);
    }

    // Lê todos os tokens numéricos de uma vez. Isso torna o parser robusto tanto
    // para grafos completos (benchmark) quanto esparsos (ex.: a Fig.1 do artigo):
    // as 4 primeiras entradas são o cabeçalho, as últimas n são as demandas, e o
    // que sobra são as arestas em blocos de 5 (i j flag c1 c2).
    std::vector<double> tok;
    for (double v; in >> v;) tok.push_back(v);

    if (tok.size() < 4) {
        throw std::runtime_error("formato inválido: cabeçalho incompleto");
    }

    Instance inst;
    inst.n = static_cast<int>(tok[0]);
    inst.num_upgradable = static_cast<int>(tok[1]);  // 'd' do cabeçalho (informativo)
    inst.p = static_cast<int>(tok[2]);
    inst.budget = tok[3];

    const int n = inst.n;
    if (n <= 0 || inst.p <= 0 || inst.p > n) {
        throw std::runtime_error("parâmetros inválidos no cabeçalho (n, p)");
    }

    // Tokens restantes = arestas (5 cada) + demandas (n no fim).
    const long long rest = static_cast<long long>(tok.size()) - 4 - n;
    if (rest < 0 || rest % 5 != 0) {
        throw std::runtime_error("formato inválido: nº de tokens de aresta/demanda inconsistente");
    }
    const long long num_edges = rest / 5;

    const std::size_t nn = static_cast<std::size_t>(n) * static_cast<std::size_t>(n);
    inst.time.assign(nn, kInf);
    inst.cost.assign(nn, kInf);
    inst.upgradable.assign(nn, 0);
    inst.demand.assign(static_cast<std::size_t>(n), 0.0);

    // Diagonal: tempo/custo zero para o próprio nó.
    for (int i = 0; i < n; ++i) {
        inst.time[inst.at(i, i)] = 0.0;
        inst.cost[inst.at(i, i)] = 0.0;
    }

    // Arestas: i j flag c1 c2  (i, j são 1-indexados no arquivo).
    std::size_t pos = 4;
    int read_upgradable = 0;
    for (long long e = 0; e < num_edges; ++e) {
        int i = static_cast<int>(tok[pos++]) - 1;  // 1-indexado -> 0-indexado
        int j = static_cast<int>(tok[pos++]) - 1;
        int flag = static_cast<int>(tok[pos++]);
        double c1 = tok[pos++];
        double c2 = tok[pos++];

        if (i < 0 || i >= n || j < 0 || j >= n) {
            throw std::runtime_error("índice de aresta fora do intervalo");
        }
        const int idx = inst.at(i, j);
        inst.time[idx] = c1;
        inst.cost[idx] = c2;
        inst.upgradable[idx] = (flag != 0) ? 1 : 0;
        if (flag != 0) ++read_upgradable;
    }

    // Linha final: demandas por nó.
    for (int i = 0; i < n; ++i) {
        inst.demand[static_cast<std::size_t>(i)] = tok[pos++];
    }

    // Confia na contagem real de flags lidas.
    inst.num_upgradable = read_upgradable;
    return inst;
}

}  // namespace ipmu

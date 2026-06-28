#pragma once

#include <limits>
#include <string>
#include <vector>

namespace ipmu {

constexpr double kInf = std::numeric_limits<double>::infinity();

// Dados crus de uma instância do IpMU, no formato do benchmark
// (Salazar et al., 2026). As matrizes n x n são guardadas em vetores planos,
// indexados por at(i, j) = i * n + j.
//
// Formato do arquivo:
//   linha 1: n            (nº de nós)
//   linha 2: d            (nº de arestas atualizáveis)
//   linha 3: p            (nº de medianas a selecionar)
//   linha 4: B            (orçamento de upgrade)
//   linhas i j flag c1 c2  (1-indexado; flag=presença do arco em A; c1=tempo; c2=custo)
//   linha final: d_1 ... d_n         (demanda de cada nó)
//
// O grafo A é ESPARSO: só as linhas flag=1 são arcos de A (|A|=m). As linhas
// flag=0 NÃO são arcos e são descartadas no parse (ficam kInf). Todo arco
// presente é atualizável (recebe upgrade até o teto u_a = u_factor·c²).
struct Instance {
    int n = 0;                       // número de nós
    int p = 0;                       // número de medianas
    int num_upgradable = 0;          // nº de arcos de A (= m, arcos flag=1 lidos)
    double budget = 0.0;             // 'B'
    double u_factor = 0.5;           // teto do upgrade: u_a = u_factor·c²_a
                                     // (0.5 = benchmark Espejo; 1.0 = âncora Fig.1)

    std::vector<double> demand;      // tamanho n
    std::vector<double> time;        // n*n, tempo c1 (kInf se arco ausente)
    std::vector<double> cost;        // n*n, custo c2 (kInf se arco ausente)
    std::vector<char> upgradable;    // n*n, 1 se (u,v) é arco de A (todo arco é atualizável)

    int at(int i, int j) const { return i * n + j; }
};

// Lê e valida uma instância do disco. Lança std::runtime_error em erro de formato.
Instance read_instance(const std::string& path);

}  // namespace ipmu

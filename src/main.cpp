#include <cstdlib>
#include <iostream>
#include <string>

#include "construction/grasp_construction.hpp"
#include "core/instance.hpp"
#include "core/problem.hpp"
#include "core/solution.hpp"
#include "localsearch/swap_local_search.hpp"
#include "metaheuristics/vns.hpp"
#include "shaking/shaking.hpp"
#include "util/json_writer.hpp"
#include "util/rng.hpp"

namespace {

void print_usage(const char* prog) {
    std::cerr
        << "Uso: " << prog << " <instancia> [opções]\n"
        << "  --alg <bvns|rvns>     metaheurística (padrão: bvns)\n"
        << "  --shake <random|greedy>  estratégia de shaking (padrão: random)\n"
        << "  --alpha <A>           voracidade da construção GRASP (padrão: 0.51)\n"
        << "  --kmax <K>            máx. de trocas no shaking (padrão: p)\n"
        << "  --iters <N>           máx. de iterações (padrão: 100)\n"
        << "  --no-improve <N>      máx. iterações sem melhora (padrão: 29)\n"
        << "  --seed <S>            semente do RNG (padrão: 42)\n"
        << "  --out <arquivo.json>  grava a solução para a visualização Python\n";
}

// Lê o valor que segue uma flag; aborta com erro se ausente.
std::string need_value(int argc, char** argv, int& i, const std::string& flag) {
    if (i + 1 >= argc) {
        std::cerr << "erro: faltou o valor de " << flag << "\n";
        std::exit(2);
    }
    return argv[++i];
}

}  // namespace

int main(int argc, char** argv) {
    using namespace ipmu;

    if (argc < 2) {
        print_usage(argv[0]);
        return 2;
    }

    std::string instance_path;
    std::string alg = "bvns";
    std::string shake_name = "random";
    std::string out_path;
    double alpha = 0.51;
    VnsParams params;  // k_max=0 (=> p), max_iters=100, max_iters_no_improve=29
    unsigned seed = 42;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--alg") {
            alg = need_value(argc, argv, i, arg);
        } else if (arg == "--shake") {
            shake_name = need_value(argc, argv, i, arg);
        } else if (arg == "--alpha") {
            alpha = std::stod(need_value(argc, argv, i, arg));
        } else if (arg == "--kmax") {
            params.k_max = std::stoi(need_value(argc, argv, i, arg));
        } else if (arg == "--iters") {
            params.max_iters = std::stol(need_value(argc, argv, i, arg));
        } else if (arg == "--no-improve") {
            params.max_iters_no_improve = std::stol(need_value(argc, argv, i, arg));
        } else if (arg == "--seed") {
            seed = static_cast<unsigned>(std::stoul(need_value(argc, argv, i, arg)));
        } else if (arg == "--out") {
            out_path = need_value(argc, argv, i, arg);
        } else if (arg == "-h" || arg == "--help") {
            print_usage(argv[0]);
            return 0;
        } else if (!arg.empty() && arg[0] == '-') {
            std::cerr << "erro: opção desconhecida " << arg << "\n";
            return 2;
        } else {
            instance_path = arg;
        }
    }

    if (instance_path.empty()) {
        print_usage(argv[0]);
        return 2;
    }

    try {
        const Instance inst = read_instance(instance_path);
        const Problem prob(inst);
        Rng rng(seed);

        std::cout << "Instância: " << instance_path << "\n"
                  << "  n=" << prob.n() << "  p=" << prob.p()
                  << "  B=" << prob.budget()
                  << "  arestas atualizáveis=" << inst.num_upgradable << "\n";

        // Solução inicial via construção GRASP.
        const Solution initial = construct_grasp(prob, alpha, rng);
        std::cout << "Construção (alpha=" << alpha << "): f=" << initial.objective << "\n";

        // Busca local plugável.
        LocalSearchFn local_search = [](const Problem& p, Solution s) {
            return local_search_swap(p, std::move(s));
        };
        const ShakeFn shake = make_shaking(shake_name);

        VnsResult result;
        if (alg == "bvns") {
            result = run_bvns(prob, initial, params, shake, local_search, rng);
        } else if (alg == "rvns") {
            result = run_rvns(prob, initial, params, shake, rng);
        } else {
            std::cerr << "erro: algoritmo desconhecido '" << alg << "'\n";
            return 2;
        }

        std::cout << "Algoritmo: " << alg << "  (shaking=" << shake_name << ")\n"
                  << "  iterações=" << result.iters
                  << "  objetivo=" << result.best.objective << "\n  medianas:";
        for (int m : result.best.medians) std::cout << " " << m;
        std::cout << "\n";

        if (!out_path.empty()) {
            const SolutionDetail detail = evaluate_detailed(prob, result.best.medians);
            write_solution_json(out_path, instance_path, prob, result.best.medians, detail);
            std::cout << "Solução gravada em: " << out_path << "\n";
        }
    } catch (const std::exception& e) {
        std::cerr << "erro: " << e.what() << "\n";
        return 1;
    }

    return 0;
}

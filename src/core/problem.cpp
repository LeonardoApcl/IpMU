#include "core/problem.hpp"

namespace ipmu {

namespace {

constexpr double kEps = 1e-9;

// (t1, c1) é lexicograficamente menor que (t2, c2)? Tempo primeiro, custo no empate.
bool lex_less(double t1, double c1, double t2, double c2) {
    if (t1 < t2 - kEps) return true;
    if (t1 > t2 + kEps) return false;
    return c1 < c2 - kEps;
}

}  // namespace

Problem::Problem(Instance instance) : inst_(std::move(instance)) {
    const int n = inst_.n;
    const std::size_t nn = static_cast<std::size_t>(n) * static_cast<std::size_t>(n);

    dist_time_ = inst_.time;  // copia inicial (arestas diretas + diagonal 0, kInf no resto)
    dist_cost_ = inst_.cost;
    next_.assign(nn, -1);

    // Sucessor inicial: se há aresta direta i->j, o próximo nó é o próprio j.
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i != j && dist_time_[idx(i, j)] < kInf) {
                next_[idx(i, j)] = j;
            }
        }
    }

    // Floyd-Warshall lexicográfico sobre (tempo, custo).
    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            const double tik = dist_time_[idx(i, k)];
            if (tik >= kInf) continue;  // poda: i não alcança k
            const double cik = dist_cost_[idx(i, k)];
            for (int j = 0; j < n; ++j) {
                const double tkj = dist_time_[idx(k, j)];
                if (tkj >= kInf) continue;
                const double cand_t = tik + tkj;
                const double cand_c = cik + dist_cost_[idx(k, j)];
                if (lex_less(cand_t, cand_c, dist_time_[idx(i, j)], dist_cost_[idx(i, j)])) {
                    dist_time_[idx(i, j)] = cand_t;
                    dist_cost_[idx(i, j)] = cand_c;
                    next_[idx(i, j)] = next_[idx(i, k)];
                }
            }
        }
    }
}

std::vector<Edge> Problem::path_edges(int from, int to) const {
    std::vector<Edge> edges;
    if (from == to || next_[idx(from, to)] == -1) {
        return edges;
    }
    int cur = from;
    while (cur != to) {
        const int nxt = next_[idx(cur, to)];
        edges.emplace_back(cur, nxt);
        cur = nxt;
    }
    return edges;
}

}  // namespace ipmu

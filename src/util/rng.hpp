#pragma once

#include <cstdint>
#include <random>
#include <vector>

namespace ipmu {

// Pequeno wrapper sobre <random> para reprodutibilidade (equivalente ao
// random.seed(...) usado no protótipo Python). Centraliza o gerador para que
// construção, busca local e shaking compartilhem a mesma sequência semeada.
class Rng {
public:
    explicit Rng(std::uint32_t seed = 42u) : engine_(seed) {}

    // Inteiro uniforme em [0, n).
    int next_index(int n) {
        std::uniform_int_distribution<int> dist(0, n - 1);
        return dist(engine_);
    }

    // Escolhe um elemento aleatório de um vetor não vazio.
    template <typename T>
    const T& choice(const std::vector<T>& v) {
        return v[static_cast<std::size_t>(next_index(static_cast<int>(v.size())))];
    }

    std::mt19937& engine() { return engine_; }

private:
    std::mt19937 engine_;
};

}  // namespace ipmu

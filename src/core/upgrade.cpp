#include "core/upgrade.hpp"

#include <algorithm>

namespace ipmu {

double relax_edges(std::vector<UpgradeItem>& items, double budget,
                   std::vector<std::tuple<int, int, double>>* upgraded) {
    // Maior benefício por unidade (W) primeiro.
    std::sort(items.begin(), items.end(),
              [](const UpgradeItem& a, const UpgradeItem& b) { return a.weight > b.weight; });

    double remaining = budget;
    double savings = 0.0;
    for (const UpgradeItem& it : items) {
        if (remaining <= 0.0) break;
        const double x = std::min(it.cost, remaining);  // teto = custo (reduz até 0)
        if (x <= 0.0) continue;
        savings += x * it.weight;
        remaining -= x;
        if (upgraded != nullptr) {
            upgraded->emplace_back(it.edge.first, it.edge.second, it.cost - x);
        }
    }
    return savings;
}

}  // namespace ipmu

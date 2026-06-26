#include "util/json_writer.hpp"

#include <fstream>
#include <stdexcept>

namespace ipmu {

namespace {

// Escapa aspas/barras de uma string para JSON.
std::string json_escape(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);
    for (char c : s) {
        if (c == '\\' || c == '"') out.push_back('\\');
        out.push_back(c);
    }
    return out;
}

}  // namespace

void write_solution_json(const std::string& path, const std::string& instance_path,
                         const Problem& prob, const std::vector<int>& medians,
                         const SolutionDetail& detail) {
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("não foi possível gravar o JSON: " + path);
    }
    out.precision(10);

    out << "{\n";
    out << "  \"instance\": \"" << json_escape(instance_path) << "\",\n";
    out << "  \"n\": " << prob.n() << ",\n";
    out << "  \"p\": " << prob.p() << ",\n";
    out << "  \"budget\": " << prob.budget() << ",\n";
    out << "  \"objective\": " << detail.objective << ",\n";

    out << "  \"medians\": [";
    for (std::size_t i = 0; i < medians.size(); ++i) {
        if (i) out << ", ";
        out << medians[i];
    }
    out << "],\n";

    out << "  \"active_edges\": [";
    for (std::size_t i = 0; i < detail.active_edges.size(); ++i) {
        if (i) out << ", ";
        out << "[" << detail.active_edges[i].first << ", "
            << detail.active_edges[i].second << "]";
    }
    out << "],\n";

    out << "  \"upgraded_edges\": [";
    for (std::size_t i = 0; i < detail.upgraded_edges.size(); ++i) {
        if (i) out << ", ";
        const auto& [u, v, new_cost] = detail.upgraded_edges[i];
        out << "[" << u << ", " << v << ", " << new_cost << "]";
    }
    out << "]\n";

    out << "}\n";
}

}  // namespace ipmu

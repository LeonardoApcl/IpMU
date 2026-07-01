"""Gera a figura de escalabilidade do artigo (tempo medio x tamanho da instancia)
a partir do resumo consolidado de seeds.

Uso:
    python python/figura_escalabilidade.py [tipo] [base_saida]

  tipo       : P ou R (padrao R, que casa com os numeros citados no texto:
               GRASP ~208 s e RVNS < 1 s em n=500).
  base_saida : caminho base sem extensao (padrao DOCS/tempo_vs_n).

Le results/report/seeds_summary.csv (colunas: Faixa,n,Tipo,Metodo,n_inst,
Avg_F(S),T(sec),...), filtra um tipo de instancia e plota o tempo medio de
execucao de cada metodo em funcao de n, em escala log-log. Salva <base>.pdf
(vetorial, para o LaTeX) e <base>.png (preview 200 DPI). Nenhuma logica de
otimizacao vive aqui. Defina MPLBACKEND=Agg para nao abrir janela.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use(os.environ.get("MPLBACKEND", "Agg"))
import matplotlib.pyplot as plt  # noqa: E402

# Diretorio raiz do repositorio (pai de python/).
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_RESUMO = os.path.join(RAIZ, "results", "report", "seeds_summary.csv")

# Ordem fixa de apresentacao + estilo por metodo (consistente com as tabelas).
METODOS = ["GRASP", "BVNS-R", "BVNS-G", "RVNS-R", "RVNS-G"]
ESTILO = {
    "GRASP":  dict(color="#1f77b4", marker="o", linestyle="-"),
    "BVNS-R": dict(color="#d62728", marker="s", linestyle="-"),
    "BVNS-G": dict(color="#ff7f0e", marker="^", linestyle="--"),
    "RVNS-R": dict(color="#2ca02c", marker="D", linestyle="-"),
    "RVNS-G": dict(color="#9467bd", marker="v", linestyle="--"),
}


def ler_tempos(tipo):
    """Retorna {metodo: [(n, T_seg), ...] ordenado por n} para o tipo dado."""
    dados = {m: {} for m in METODOS}
    with open(CSV_RESUMO, "r", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha["Tipo"] != tipo:
                continue
            metodo = linha["Metodo"]
            if metodo not in dados:
                continue
            dados[metodo][int(linha["n"])] = float(linha["T(sec)"])
    return {m: sorted(d.items()) for m, d in dados.items()}


def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "R"
    base_saida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "DOCS", "tempo_vs_n")

    dados = ler_tempos(tipo)

    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    enes = set()
    for metodo in METODOS:
        pares = dados[metodo]
        if not pares:
            continue
        xs = [n for n, _ in pares]
        ys = [t for _, t in pares]
        enes.update(xs)
        ax.plot(xs, ys, label=metodo, markersize=5, linewidth=1.5, **ESTILO[metodo])

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Tamanho da instância $n$")
    ax.set_ylabel("Tempo médio de execução (s)")

    enes = sorted(enes)
    ax.set_xticks(enes)
    ax.set_xticklabels([str(n) for n in enes])
    ax.minorticks_off()

    ax.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.6)
    ax.legend(frameon=False, ncol=2, fontsize=9)
    fig.tight_layout()

    diretorio = os.path.dirname(base_saida)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    pdf = base_saida + ".pdf"
    png = base_saida + ".png"
    fig.savefig(pdf)
    fig.savefig(png, dpi=200)
    plt.close(fig)

    print(f"Tipo: {tipo}  |  n = {enes}")
    print(f"Figura salva em:\n  {pdf}\n  {png}")


if __name__ == "__main__":
    main()

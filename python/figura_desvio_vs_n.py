"""Gera a figura de corretude da solução (desvio % vs SOTA x tamanho da
instância) a partir do resumo consolidado de seeds, com os tipos P e R lado a
lado no mesmo par de arquivos.

Uso:
    python python/figura_desvio_vs_n.py [base_saida]

  base_saida : caminho base sem extensão (padrão DOCS/desvio_vs_n).

Lê results/report/seeds_summary.csv (colunas: Faixa,n,Tipo,Metodo,n_inst,
Avg_F(S),T(sec),Dev_med_%,...) e plota o desvio médio (sobre as seeds) em
relação ao SOTA de cada método em função de n, em dois painéis (P e R),
escala log no eixo x. Linhas sem SOTA publicado (Dev_med_% vazio — caso de
R n=200 e de todo n=500) são simplesmente omitidas: cada painel só cobre os n
onde existe referência de otimalidade. Salva <base>.pdf (vetorial, para o
LaTeX) e <base>.png (preview 200 DPI). Nenhuma lógica de otimização vive
aqui. Defina MPLBACKEND=Agg para não abrir janela.
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

# Ordem fixa de apresentacao + estilo por metodo (consistente com as tabelas
# e com python/figura_escalabilidade.py).
METODOS = ["GRASP", "BVNS-R", "BVNS-G", "RVNS-R", "RVNS-G"]
ESTILO = {
    "GRASP":  dict(color="#1f77b4", marker="o", linestyle="-"),
    "BVNS-R": dict(color="#d62728", marker="s", linestyle="-"),
    "BVNS-G": dict(color="#ff7f0e", marker="^", linestyle="--"),
    "RVNS-R": dict(color="#2ca02c", marker="D", linestyle="-"),
    "RVNS-G": dict(color="#9467bd", marker="v", linestyle="--"),
}
TITULOS = {"P": "Instâncias P", "R": "Instâncias R"}


def ler_desvios(tipo):
    """Retorna {metodo: [(n, Dev_med_%), ...] ordenado por n} para o tipo dado.

    Linhas com Dev_med_% vazio (sem SOTA publicado para aquele n) sao puladas.
    """
    dados = {m: {} for m in METODOS}
    with open(CSV_RESUMO, "r", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha["Tipo"] != tipo:
                continue
            metodo = linha["Metodo"]
            if metodo not in dados:
                continue
            dev = linha["Dev_med_%"]
            if dev == "":
                continue
            dados[metodo][int(linha["n"])] = float(dev)
    return {m: sorted(d.items()) for m, d in dados.items()}


def plotar_painel(ax, tipo):
    """Desenha as linhas de todos os metodos para um tipo (P ou R) em ax."""
    dados = ler_desvios(tipo)
    enes = set()
    for metodo in METODOS:
        pares = dados[metodo]
        if not pares:
            continue
        xs = [n for n, _ in pares]
        ys = [d for _, d in pares]
        enes.update(xs)
        ax.plot(xs, ys, label=metodo, markersize=5, linewidth=1.5, **ESTILO[metodo])

    ax.axhline(0, color="grey", linewidth=0.8, linestyle=":")
    ax.set_xscale("log")
    # symlog: linear perto de 0 (onde GRASP/BVNS ficam colados numa escala
    # linear comum) e log a partir de linthresh, comprimindo a cauda de
    # RVNS-R sem cortar dados nem exigir eixo quebrado.
    ax.set_yscale("symlog", linthresh=0.01, linscale=0.5)
    ax.set_xlabel(r"Tamanho da instância $n$")
    ax.set_title(TITULOS[tipo])

    enes = sorted(enes)
    ax.set_xticks(enes)
    ax.set_xticklabels([str(n) for n in enes])
    ax.minorticks_off()
    ax.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.6)
    return enes


def main():
    base_saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "figuras", "desvio_vs_n")

    fig, (ax_p, ax_r) = plt.subplots(1, 2, figsize=(10.0, 4.0), sharey=True)
    enes_p = plotar_painel(ax_p, "P")
    enes_r = plotar_painel(ax_r, "R")
    ax_p.set_ylabel("Desvio médio em relação ao SOTA (%)")

    handles, labels = ax_p.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.08, 1, 1))

    diretorio = os.path.dirname(base_saida)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    pdf = base_saida + ".pdf"
    png = base_saida + ".png"
    fig.savefig(pdf)
    fig.savefig(png, dpi=200)
    plt.close(fig)

    print(f"Tipo P: n = {enes_p}")
    print(f"Tipo R: n = {enes_r}")
    print(f"Figura salva em:\n  {pdf}\n  {png}")


if __name__ == "__main__":
    main()

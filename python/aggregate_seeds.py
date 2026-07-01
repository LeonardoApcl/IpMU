"""Agrega os checkpoints multi-seed do benchmark em estatísticas e nas tabelas
do artigo.

Lê `results/raw/<config>_seed<s>.csv` (todas as seeds disponíveis, ou as de
`--seeds`) e produz duas camadas:

  2a. Detalhe por (instância, método) — `results/report/seeds_detail_<config>.csv`:
      n_seeds, F_média, F_desvio (estabilidade), F_melhor, F_pior, SOTA,
      Dev_média, Dev_melhor.

  2b. Tabela-resumo no formato do artigo — uma linha por (Tipo, Método) dentro de
      cada n, agregando sobre as instâncias do grupo. Colunas:
      Tipo | Método | Avg F(S) | T(sec) | Dev méd (%) | Dev melhor (%) | # Opt
      (+ F_desvio médio como medida de estabilidade). Emitida separada por faixa:
      `seeds_summary_small.csv` (n<=80) e `seeds_summary_big.csv` (n>=100), mais
      um `seeds_summary.csv` "tidy" com n/Faixa como colunas para pivotar.

O gap (Dev) é calculado contra a coluna SOTA do .xlsx do artigo (mesma referência
e fórmula dos relatórios atuais — `build_report`): Dev = (F - SOTA)/SOTA. Nas n<=80
o SOTA é ótimo-provado (otimalidade real); nas n>=100 é o melhor-conhecido publicado
("ótimo" = "atingiu o melhor-conhecido"). Instâncias sem SOTA (corrSergio/randomSergio)
ficam com Dev vazio e fora da contagem de # Opt.

Exemplos:
  python\\aggregate_seeds.py
  python\\aggregate_seeds.py --seeds 42 43 44 45 46 47 48 49 50 51
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_benchmark import REPO, load_sota  # noqa: E402

# Ordem e rótulos amigáveis dos métodos (linhas das tabelas).
CONFIG_ORDER = ["salazar", "bvns_random", "bvns_greedy", "rvns_random", "rvns_greedy"]
METHOD_LABEL = {
    "salazar": "GRASP",
    "bvns_random": "BVNS-R",
    "bvns_greedy": "BVNS-G",
    "rvns_random": "RVNS-R",
    "rvns_greedy": "RVNS-G",
}

SMALL_MAX = 80  # n<=SMALL_MAX = "pequenas" (SOTA ótimo-provado); >= 100 = "grandes".

DETAIL_FIELDS = [
    "Instancia", "Tipo", "n", "n_seeds",
    "F_media", "F_desvio", "F_melhor", "F_pior",
    "SOTA", "Dev_media", "Dev_melhor",
]
SUMMARY_FIELDS = [
    "Faixa", "n", "Tipo", "Metodo",
    "n_inst", "Avg_F(S)", "T(sec)",
    "Dev_med_%", "Dev_melhor_%", "#Opt", "F_desvio_med",
]


def tipo_from_rel(rel: str) -> str:
    """Deriva o tipo P/R da instância.

    Primeiro pelo componente de diretório 'P'/'R' (pequenas e big n=100/200);
    senão pelo nome do arquivo (n=500 fica em BigInstances500[\\BigInstancesCorrelated]
    sem subpasta P/R): corrSergio/`_cp_` = P (correlacionado), randomSergio/`_ca_` = R.
    """
    parts = re.split(r"[\\/]", rel)
    for p in parts:
        if p in ("P", "R"):
            return p
    low = rel.lower()
    if "corrsergio" in low or "_cp_" in low:
        return "P"
    if "randomsergio" in low or "_ca_" in low:
        return "R"
    return "?"


def discover_seeds(raw_dir: Path) -> list:
    """Seeds presentes em results/raw/ (a partir dos nomes <config>_seed<s>.csv)."""
    seeds = set()
    for p in raw_dir.glob("*_seed*.csv"):
        m = re.search(r"_seed(\d+)\.csv$", p.name)
        if m:
            seeds.add(int(m.group(1)))
    return sorted(seeds)


def read_config(raw_dir: Path, cfg: str, seeds: list) -> dict:
    """basename -> {n, tipo, F:[obj por seed], T:[tempo por seed]} para uma config."""
    data: dict = {}
    for seed in seeds:
        p = raw_dir / f"{cfg}_seed{seed}.csv"
        if not p.exists():
            continue
        with p.open("r", newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                b = r["basename"]
                d = data.setdefault(b, {
                    "n": int(r["grupo"]),
                    "tipo": tipo_from_rel(r["instancia_rel"]),
                    "F": [], "T": [],
                })
                try:
                    d["F"].append(float(r["objetivo"]))
                    d["T"].append(float(r["tempo_s"]))
                except (KeyError, ValueError):
                    pass
    return data


def instance_stats(d: dict, sota_fs):
    """Estatísticas por instância sobre as seeds. Retorna dict com F_*/Dev_*."""
    F = d["F"]
    f_media = statistics.mean(F)
    f_desvio = statistics.stdev(F) if len(F) >= 2 else 0.0
    f_melhor = min(F)
    f_pior = max(F)
    dev_media = (f_media - sota_fs) / sota_fs if sota_fs else None
    dev_melhor = (f_melhor - sota_fs) / sota_fs if sota_fs else None
    return {
        "n_seeds": len(F), "F_media": f_media, "F_desvio": f_desvio,
        "F_melhor": f_melhor, "F_pior": f_pior,
        "Dev_media": dev_media, "Dev_melhor": dev_melhor,
        "T_media": statistics.mean(d["T"]) if d["T"] else 0.0,
    }


def main(argv=None):
    pa = argparse.ArgumentParser(
        description="Agrega checkpoints multi-seed em estatísticas e tabelas do artigo.")
    pa.add_argument("--raw-dir", default=str(REPO / "results" / "raw"))
    pa.add_argument("--report-dir", default=str(REPO / "results" / "report"))
    pa.add_argument("--sota", default=str(REPO / "results" / "ResultsInstanceByInstance.xlsx"))
    pa.add_argument("--seeds", nargs="+", type=int, default=None,
                    help="seeds a agregar. Padrão: todas as presentes em raw/.")
    pa.add_argument("--tol", type=float, default=1e-6,
                    help="tolerância de # Opt (F_melhor <= SOTA*(1+tol)).")
    pa.add_argument("--small-max", type=int, default=SMALL_MAX,
                    help=f"maior n da faixa 'pequenas' (padrão {SMALL_MAX}).")
    a = pa.parse_args(argv)

    raw_dir = Path(a.raw_dir)
    report_dir = Path(a.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    sota = load_sota(Path(a.sota))

    seeds = a.seeds if a.seeds else discover_seeds(raw_dir)
    if not seeds:
        print(f"nenhum checkpoint *_seed*.csv em {raw_dir}.", file=sys.stderr)
        return 1
    print(f"agregando seeds: {seeds}  | SOTA: {len(sota)} instâncias de referência")

    # group key (faixa, n, tipo, cfg) -> lista de stats por instância (+ flags)
    summary: dict = {}
    n_seeds_seen = set()

    for cfg in CONFIG_ORDER:
        data = read_config(raw_dir, cfg, seeds)
        if not data:
            continue
        # 2a — detalhe por instância
        detail_path = report_dir / f"seeds_detail_{cfg}.csv"
        with detail_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=DETAIL_FIELDS)
            w.writeheader()
            for b in sorted(data):
                d = data[b]
                ref = sota.get(b)
                sota_fs = ref[0] if ref else None
                st = instance_stats(d, sota_fs)
                n_seeds_seen.add(st["n_seeds"])
                w.writerow({
                    "Instancia": b, "Tipo": d["tipo"], "n": d["n"],
                    "n_seeds": st["n_seeds"],
                    "F_media": st["F_media"], "F_desvio": st["F_desvio"],
                    "F_melhor": st["F_melhor"], "F_pior": st["F_pior"],
                    "SOTA": "" if sota_fs is None else sota_fs,
                    "Dev_media": "" if st["Dev_media"] is None else st["Dev_media"],
                    "Dev_melhor": "" if st["Dev_melhor"] is None else st["Dev_melhor"],
                })
                # acumula para o resumo 2b
                faixa = "pequenas" if d["n"] <= a.small_max else "grandes"
                key = (faixa, d["n"], d["tipo"], cfg)
                rec = summary.setdefault(key, {
                    "F_media": [], "T_media": [], "F_desvio": [],
                    "Dev_media": [], "Dev_melhor": [], "n_inst": 0, "n_opt": 0,
                })
                rec["n_inst"] += 1
                rec["F_media"].append(st["F_media"])
                rec["T_media"].append(st["T_media"])
                rec["F_desvio"].append(st["F_desvio"])
                if sota_fs:
                    rec["Dev_media"].append(st["Dev_media"])
                    rec["Dev_melhor"].append(st["Dev_melhor"])
                    if st["F_melhor"] <= sota_fs * (1 + a.tol):
                        rec["n_opt"] += 1
        print(f"detalhe: {detail_path}  ({len(data)} instâncias)")

    if not summary:
        print("nada a resumir.", file=sys.stderr)
        return 1

    # 2b — tabela-resumo (linha por Tipo×Método dentro de cada n)
    def avg(xs):
        return statistics.mean(xs) if xs else None

    rows = []
    for (faixa, n, tipo, cfg), rec in summary.items():
        rows.append({
            "Faixa": faixa, "n": n, "Tipo": tipo, "Metodo": METHOD_LABEL.get(cfg, cfg),
            "n_inst": rec["n_inst"],
            "Avg_F(S)": avg(rec["F_media"]),
            "T(sec)": avg(rec["T_media"]),
            "Dev_med_%": (avg(rec["Dev_media"]) * 100) if rec["Dev_media"] else "",
            "Dev_melhor_%": (avg(rec["Dev_melhor"]) * 100) if rec["Dev_melhor"] else "",
            "#Opt": rec["n_opt"] if rec["Dev_media"] else "",
            "F_desvio_med": avg(rec["F_desvio"]),
        })

    method_rank = {METHOD_LABEL[c]: i for i, c in enumerate(CONFIG_ORDER)}
    rows.sort(key=lambda r: (r["n"], r["Tipo"], method_rank.get(r["Metodo"], 99)))

    def write_summary(path, subset):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDS)
            w.writeheader()
            for r in subset:
                w.writerow(r)
        print(f"resumo: {path}  ({len(subset)} linhas)")

    write_summary(report_dir / "seeds_summary.csv", rows)
    write_summary(report_dir / "seeds_summary_small.csv",
                  [r for r in rows if r["Faixa"] == "pequenas"])
    write_summary(report_dir / "seeds_summary_big.csv",
                  [r for r in rows if r["Faixa"] == "grandes"])

    if n_seeds_seen:
        lo, hi = min(n_seeds_seen), max(n_seeds_seen)
        nota = f"{lo}" if lo == hi else f"{lo}–{hi} (incompleto p/ algumas instâncias)"
        print(f"n_seeds por instância: {nota}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Runner de benchmark completo do IpMU — 5 configurações, pausável e retomável.

Compara as 4 variantes do VNS (bvns/rvns × random/greedy) e o GRASP do artigo
de Salazar (--alg salazar) em todas as instâncias. Cada configuração tem seu
próprio checkpoint CSV independente em results/raw/; pausar (Ctrl+C) e reexecutar
retoma a partir do ponto de parada sem refazer trabalho concluído.

Exemplos:
  python\\run_full_benchmark.py
  python\\run_full_benchmark.py --instances instances\\P\\n=20
  python\\run_full_benchmark.py --configs bvns_random salazar
  python\\run_full_benchmark.py --report-only
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Garante importação mesmo quando invocado de dentro de python/.
sys.path.insert(0, str(Path(__file__).parent))

from run_benchmark import (  # noqa: E402
    REPO, RAW_FIELDS,
    enumerate_instances, load_done, open_raw_writer, run_solver,
    load_sota, build_report,
)

# --------------------------------------------------------------------------- #
# Configurações do benchmark completo (5)
# --------------------------------------------------------------------------- #

ALL_CONFIGS = [
    {"name": "bvns_random",  "alg": "bvns",    "shake": "random"},
    {"name": "bvns_greedy",  "alg": "bvns",    "shake": "greedy"},
    {"name": "rvns_random",  "alg": "rvns",    "shake": "random"},
    {"name": "rvns_greedy",  "alg": "rvns",    "shake": "greedy"},
    {"name": "salazar",      "alg": "salazar", "shake": None},
]

CONFIG_NAMES = [c["name"] for c in ALL_CONFIGS]

COMBINED_FIELDS = ["Instancia"] + CONFIG_NAMES + ["SOTA", "melhor_config", "Dev_melhor"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def build_solver_args(cfg: dict, seed: int, extra: dict) -> list:
    args = ["--alg", cfg["alg"], "--seed", str(seed)]
    if cfg["shake"] is not None:
        args += ["--shake", cfg["shake"]]
    if extra.get("alpha") is not None:
        args += ["--alpha", str(extra["alpha"])]
    if extra.get("kmax") is not None:
        args += ["--kmax", str(extra["kmax"])]
    if extra.get("iters") is not None:
        args += ["--iters", str(extra["iters"])]
    if extra.get("no_improve") is not None:
        args += ["--no-improve", str(extra["no_improve"])]
    return args


# --------------------------------------------------------------------------- #
# Execução paralela (pool de workers; uma tarefa = um run instância×config×seed)
# --------------------------------------------------------------------------- #

def load_duration_estimates(raw_dir: Path, cfg_name: str) -> dict:
    """tempo_s por basename a partir de QUALQUER checkpoint já existente da config
    (qualquer seed). Usado só para ordenar as tarefas longest-first."""
    est: dict = {}
    for p in sorted(raw_dir.glob(f"{cfg_name}_seed*.csv")):
        try:
            with p.open("r", newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        est[row["basename"]] = float(row["tempo_s"])
                    except (KeyError, ValueError):
                        pass
        except OSError:
            pass
    return est


def build_tasks(configs: list, instances: list, raw_dir: Path,
                seeds: list, extra: dict) -> list:
    """Tarefas pendentes (config, seed, instância) ainda fora do checkpoint,
    ordenadas por duração estimada decrescente (longest-first) para saturar os
    núcleos e dissolver a cauda das instâncias grandes."""
    BIG = 1e9  # desconhecidas (ex.: corrSergio/randomSergio) vão primeiro
    tasks: list = []
    for cfg in configs:
        est = load_duration_estimates(raw_dir, cfg["name"])
        for seed in seeds:
            raw_path = raw_dir / f"{cfg['name']}_seed{seed}.csv"
            done = load_done(raw_path)
            args = build_solver_args(cfg, seed, extra)
            for f, info in instances:
                rel = os.path.relpath(f, REPO)
                if rel in done:
                    continue
                tasks.append({
                    "cfg": cfg, "seed": seed, "f": f, "info": info,
                    "rel": rel, "args": args, "dur": est.get(info[0], BIG),
                })
    tasks.sort(key=lambda t: t["dur"], reverse=True)
    return tasks


def run_parallel(configs: list, instances: list, exe: Path, raw_dir: Path,
                 seeds: list, extra: dict, jobs: int) -> None:
    tasks = build_tasks(configs, instances, raw_dir, seeds, extra)
    total = len(tasks)
    if total == 0:
        print("nada pendente: todos os (config, seed, instância) já no checkpoint.")
        return
    print(f"tarefas pendentes: {total}  |  workers: {jobs}  |  seeds: {seeds}")

    # Escritores por (config, seed), abertos sob demanda. A escrita acontece só na
    # thread principal (ao colher cada future), então não há corrida nos arquivos.
    writers: dict = {}

    def writer_for(cfg_name: str, seed: int):
        key = (cfg_name, seed)
        if key not in writers:
            writers[key] = open_raw_writer(raw_dir / f"{cfg_name}_seed{seed}.csv")
        return writers[key]

    def work(task: dict):
        obj, tempo_s = run_solver(exe, task["f"], task["args"])
        return task, obj, tempo_s

    processed = failures = 0
    t0 = time.time()
    pool = ThreadPoolExecutor(max_workers=jobs)
    futures = {pool.submit(work, t): t for t in tasks}
    try:
        for fut in as_completed(futures):
            task = futures[fut]
            cfg = task["cfg"]
            seed = task["seed"]
            base, n, m, p, B, idx = task["info"]
            try:
                _t, obj, tempo_s = fut.result()
            except Exception as e:
                failures += 1
                flog = raw_dir / f"{cfg['name']}_seed{seed}_failures.log"
                with flog.open("a", encoding="utf-8") as ff:
                    ff.write(f"{task['rel']}\t{e}\n")
                print(f"  FALHA {cfg['name']} seed{seed} {task['rel']}: {e}",
                      file=sys.stderr)
                continue
            fh, writer = writer_for(cfg["name"], seed)
            writer.writerow({
                "instancia_rel": task["rel"], "basename": base, "grupo": n,
                "p": p, "B": B, "alg": cfg["alg"], "seed": seed,
                "objetivo": repr(obj), "tempo_s": repr(tempo_s),
            })
            fh.flush()
            os.fsync(fh.fileno())
            processed += 1
            if processed % 10 == 0 or processed == total:
                el = time.time() - t0
                rate = processed / el if el else 0.0
                eta = (total - processed) / rate if rate else 0.0
                print(f"  [{processed}/{total}] {cfg['name']} seed{seed} {base}"
                      f"  f={obj:.4f} t={tempo_s:.2f}s"
                      f"  | {rate * 3600:.0f}/h ETA {eta / 3600:.1f}h")
    except KeyboardInterrupt:
        print("\ninterrompido — checkpoints preservados; gerando relatórios do progresso...")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
        for fh, _w in writers.values():
            fh.close()
    print(f"\nconcluído: {processed}/{total} runs, {failures} falhas, "
          f"{(time.time() - t0) / 3600:.2f}h de relógio.")


# --------------------------------------------------------------------------- #
# Relatório combinado (todas as configs lado a lado)
# --------------------------------------------------------------------------- #

def build_combined_report(raw_dir: Path, sota: dict, report_dir: Path,
                          seed: int, tol: float) -> None:
    """Tabela lado a lado: uma linha por instância, uma coluna por config.

    Lê os checkpoints de TODAS as configs (não só as rodadas nesta invocação),
    para que o relatório reflita sempre o estado acumulado completo.
    """
    # basename -> {config_name: obj, "grupo": n}
    data: dict = {}
    for cfg in ALL_CONFIGS:
        raw_path = raw_dir / f"{cfg['name']}_seed{seed}.csv"
        if not raw_path.exists():
            continue
        with raw_path.open("r", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                b = row["basename"]
                if b not in data:
                    data[b] = {"grupo": row["grupo"]}
                data[b][cfg["name"]] = float(row["objetivo"])

    if not data:
        print("relatório combinado: nenhum checkpoint encontrado, nada a gerar.")
        return

    by_group: dict = {}
    for b, vals in data.items():
        by_group.setdefault(vals["grupo"], []).append(b)

    report_dir.mkdir(parents=True, exist_ok=True)
    for grupo in sorted(by_group, key=lambda g: int(g)):
        out = report_dir / f"combined_n{grupo}.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COMBINED_FIELDS)
            w.writeheader()
            for b in sorted(by_group[grupo]):
                vals = data[b]
                row: dict = {"Instancia": b}
                for name in CONFIG_NAMES:
                    row[name] = vals.get(name, "")

                ref = sota.get(b)
                sota_fs = ref[0] if ref else None
                row["SOTA"] = "" if sota_fs is None else sota_fs

                # Melhor config (menor objetivo entre as disponíveis).
                objs = {name: vals[name] for name in CONFIG_NAMES if name in vals}
                if objs:
                    melhor = min(objs, key=lambda k: objs[k])
                    melhor_fs = objs[melhor]
                    row["melhor_config"] = melhor
                    row["Dev_melhor"] = (
                        "" if sota_fs is None
                        else (melhor_fs - sota_fs) / sota_fs
                    )
                else:
                    row["melhor_config"] = ""
                    row["Dev_melhor"] = ""

                w.writerow(row)
        print(f"relatório combinado: {out}  ({len(by_group[grupo])} instâncias)")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    pa = argparse.ArgumentParser(
        description="Benchmark completo IpMU: 5 configs × instâncias, pausável.")
    pa.add_argument("--instances", default=str(REPO / "instances"),
                    help="pasta raiz das instâncias (recursivo). Padrão: instances/")
    pa.add_argument("--exe", default=str(REPO / "ipmu.exe"),
                    help="caminho do ipmu.exe")
    pa.add_argument("--raw-dir", default=str(REPO / "results" / "raw"),
                    help="diretório dos checkpoints CSV")
    pa.add_argument("--sota", default=str(REPO / "results" / "ResultsInstanceByInstance.xlsx"),
                    help="planilha de referência do artigo (coluna SOTA)")
    pa.add_argument("--report-dir", default=str(REPO / "results" / "report"))
    pa.add_argument("--report-only", action="store_true",
                    help="apenas (re)gera os relatórios a partir dos checkpoints existentes")
    pa.add_argument("--tol", type=float, default=1e-6,
                    help="tolerância de isBest? (padrão: 1e-6)")
    pa.add_argument("--seed", type=int, default=42,
                    help="seed única (compat). Ignorado se --seeds for dado.")
    pa.add_argument("--seeds", nargs="+", type=int, default=None, metavar="SEED",
                    help="lista de seeds a rodar (ex.: --seeds 43 44 45). "
                         "Padrão: apenas --seed.")
    pa.add_argument("--jobs", type=int, default=6,
                    help="nº de runs do ipmu.exe em paralelo (padrão 6, p/ 6 núcleos).")
    pa.add_argument("--configs", nargs="+", choices=CONFIG_NAMES, default=None,
                    metavar="CONFIG",
                    help=("subset de configs a rodar. Padrão: todas. "
                          f"Valores: {CONFIG_NAMES}"))
    # Passthrough para o solver (--alg/--shake são fixados por config).
    pa.add_argument("--alpha", type=float, default=None)
    pa.add_argument("--kmax", type=int, default=None)
    pa.add_argument("--iters", type=int, default=None)
    pa.add_argument("--no-improve", dest="no_improve", type=int, default=None)
    a = pa.parse_args(argv)

    configs = (
        [c for c in ALL_CONFIGS if c["name"] in a.configs]
        if a.configs else ALL_CONFIGS
    )
    seeds = a.seeds if a.seeds else [a.seed]
    raw_dir = Path(a.raw_dir)
    report_dir = Path(a.report_dir)
    sota = load_sota(Path(a.sota))
    print(f"SOTA: {len(sota)} instâncias de referência carregadas.")
    extra = {
        "alpha": a.alpha, "kmax": a.kmax,
        "iters": a.iters, "no_improve": a.no_improve,
    }

    if not a.report_only:
        exe = Path(a.exe)
        if not exe.exists():
            print(f"erro: ipmu.exe não encontrado em {exe}. Rode .\\build.ps1 antes.",
                  file=sys.stderr)
            return 1

        instances = enumerate_instances(Path(a.instances))
        print(f"instâncias: {len(instances)} totais | configs: "
              f"{[c['name'] for c in configs]} | seeds: {seeds}")

        try:
            run_parallel(configs, instances, exe, raw_dir, seeds, extra, a.jobs)
        except KeyboardInterrupt:
            print("\ninterrompido — gerando relatório do progresso atual...")

    # Relatórios por seed: individuais por config + combinado.
    for seed in seeds:
        for cfg in configs:
            raw_path = raw_dir / f"{cfg['name']}_seed{seed}.csv"
            build_report(raw_path, sota, report_dir,
                         f"{cfg['name']}_seed{seed}", a.tol)
        build_combined_report(raw_dir, sota, report_dir, seed, a.tol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

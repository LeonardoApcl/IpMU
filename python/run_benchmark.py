"""Runner de benchmark do IpMU — pausável e retomável.

Resolve cada instância com o `ipmu.exe`, grava o progresso num checkpoint CSV
(append-only, com flush por instância) e gera uma tabela de comparação no
formato do artigo (join contra a coluna SOTA do .xlsx, com Dev e isBest?).

Características principais:
  * Retomada: re-executar pula as instâncias já concluídas e continua de onde
    parou. Parar (Ctrl+C) nunca perde trabalho concluído nem deixa linha pela
    metade — o checkpoint é a fonte da verdade.
  * Sem dependências externas: o .xlsx é lido como zip/XML (sem openpyxl).

Exemplos:
  python\\run_benchmark.py --alg bvns
  python\\run_benchmark.py --alg bvns --report-only
  python\\run_benchmark.py --instances "instances\\P\\n=20" --alg bvns
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Raiz do repositório (este arquivo vive em python/).
REPO = Path(__file__).resolve().parent.parent

_OBJ_RE = re.compile(r"objetivo=([-\d.eE+]+)")
_TIME_RE = re.compile(r"tempo_s=([-\d.eE+]+)")

# Colunas do checkpoint CSV (fonte da verdade, append-only).
RAW_FIELDS = [
    "instancia_rel", "basename", "grupo", "p", "B",
    "alg", "seed", "objetivo", "tempo_s",
]


# --------------------------------------------------------------------------- #
# Enumeração e parsing de nomes de instância
# --------------------------------------------------------------------------- #

def parse_instance_name(path: Path):
    """Deriva (basename, n, m, p, B, idx) do nome AUpdata_<tipo>_n_m_p_B_idx.txt.

    Os 5 últimos tokens são numéricos; o que sobra (que pode ter '_') é o tipo.
    Retorna None se o nome não casar com o padrão esperado.
    """
    base = path.stem  # sem .txt
    if not base.startswith("AUpdata_"):
        return None
    tokens = base.split("_")
    if len(tokens) < 6:
        return None
    tail = tokens[-5:]
    try:
        n, m, p, B, idx = (int(t) for t in tail)
    except ValueError:
        return None
    return base, n, m, p, B, idx


def enumerate_instances(root: Path):
    """Lista determinística (ordenada por caminho) de instâncias sob `root`."""
    files = sorted(root.rglob("*.txt"), key=lambda x: str(x).lower())
    out = []
    for f in files:
        info = parse_instance_name(f)
        if info is None:
            continue
        out.append((f, info))
    return out


# --------------------------------------------------------------------------- #
# Checkpoint (retomada)
# --------------------------------------------------------------------------- #

def load_done(raw_path: Path):
    """Conjunto de instancia_rel já concluídas (para pular na retomada)."""
    done = set()
    if not raw_path.exists():
        return done
    with raw_path.open("r", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            done.add(row["instancia_rel"])
    return done


def open_raw_writer(raw_path: Path):
    """Abre o checkpoint em modo append; escreve o cabeçalho se for novo."""
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    new = not raw_path.exists() or raw_path.stat().st_size == 0
    fh = raw_path.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fh, fieldnames=RAW_FIELDS)
    if new:
        writer.writeheader()
        fh.flush()
    return fh, writer


# --------------------------------------------------------------------------- #
# Execução do solver
# --------------------------------------------------------------------------- #

def run_solver(exe: Path, instance: Path, solver_args):
    """Executa o ipmu.exe e devolve (objetivo, tempo_s). Lança em caso de falha."""
    cmd = [str(exe), str(instance)] + solver_args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"exit {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    obj = _OBJ_RE.search(proc.stdout)
    tmp = _TIME_RE.search(proc.stdout)
    if not obj or not tmp:
        raise RuntimeError(f"saída sem objetivo/tempo_s:\n{proc.stdout}")
    return float(obj.group(1)), float(tmp.group(1))


# --------------------------------------------------------------------------- #
# Leitura do SOTA a partir do .xlsx (sem openpyxl)
# --------------------------------------------------------------------------- #

def _col_index(cell_ref: str) -> int:
    """'B3' -> 1 (0-based)."""
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def load_sota(xlsx_path: Path):
    """Mapa basename -> (sota_fs, sota_tiempo) lido de todas as abas do .xlsx."""
    if not xlsx_path.exists():
        return {}
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    sota = {}
    with zipfile.ZipFile(xlsx_path) as z:
        shared = []
        try:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(ns + "si"):
                shared.append("".join(t.text or "" for t in si.iter(ns + "t")))
        except KeyError:
            pass

        def cell_value(c):
            v = c.find(ns + "v")
            if v is None or v.text is None:
                return None
            if c.get("t") == "s":
                return shared[int(v.text)]
            return v.text

        sheets = sorted(n for n in z.namelist()
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        for name in sheets:
            sheet = ET.fromstring(z.read(name))
            data = sheet.find(ns + "sheetData")
            if data is None:
                continue
            rows = []  # cada linha: dict {col_idx: value}
            for r in data.findall(ns + "row"):
                row = {}
                for c in r.findall(ns + "c"):
                    ref = c.get("r")
                    if ref:
                        row[_col_index(ref)] = cell_value(c)
                rows.append(row)

            # Localiza a coluna do cabeçalho "SOTA" (o F(S) fica nessa mesma
            # coluna; o Tiempo na seguinte).
            sota_col = None
            for row in rows[:6]:
                for ci, val in row.items():
                    if isinstance(val, str) and val.strip().upper() == "SOTA":
                        sota_col = ci
                        break
                if sota_col is not None:
                    break
            if sota_col is None:
                continue

            # Detecta a coluna do nome da instância (a que mais contém 'AUpdata').
            name_counts = {}
            for row in rows:
                for ci, val in row.items():
                    if isinstance(val, str) and val.startswith("AUpdata"):
                        name_counts[ci] = name_counts.get(ci, 0) + 1
            if not name_counts:
                continue
            name_col = max(name_counts, key=name_counts.get)

            # Linhas de dados.
            for row in rows:
                name = row.get(name_col)
                if not isinstance(name, str) or not name.startswith("AUpdata"):
                    continue
                try:
                    fs = float(row[sota_col])
                except (KeyError, TypeError, ValueError):
                    continue
                try:
                    tiempo = float(row.get(sota_col + 1))
                except (TypeError, ValueError):
                    tiempo = None
                sota[name] = (fs, tiempo)
    return sota


# --------------------------------------------------------------------------- #
# Geração do relatório (join com SOTA -> Dev, isBest?)
# --------------------------------------------------------------------------- #

REPORT_FIELDS = [
    "Instancia", "F(S)", "Tiempo", "SOTA_FS", "SOTA_Tiempo", "Dev", "isBest?",
]


def build_report(raw_path: Path, sota, report_dir: Path, tag: str, tol: float):
    """Lê o checkpoint e escreve um CSV por grupo n no layout do artigo."""
    if not raw_path.exists():
        print("nada a reportar: checkpoint inexistente.")
        return
    by_group = {}
    with raw_path.open("r", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_group.setdefault(row["grupo"], []).append(row)

    report_dir.mkdir(parents=True, exist_ok=True)
    for grupo in sorted(by_group, key=lambda g: int(g)):
        out = report_dir / f"{tag}_n{grupo}.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=REPORT_FIELDS)
            w.writeheader()
            for r in sorted(by_group[grupo], key=lambda x: x["basename"]):
                fs = float(r["objetivo"])
                ref = sota.get(r["basename"])
                sota_fs = ref[0] if ref else None
                sota_t = ref[1] if ref else None
                dev = (fs - sota_fs) / sota_fs if sota_fs else None
                is_best = (1 if (sota_fs is not None and fs <= sota_fs * (1 + tol))
                           else (0 if sota_fs is not None else None))
                w.writerow({
                    "Instancia": r["basename"],
                    "F(S)": fs,
                    "Tiempo": r["tempo_s"],
                    "SOTA_FS": "" if sota_fs is None else sota_fs,
                    "SOTA_Tiempo": "" if sota_t is None else sota_t,
                    "Dev": "" if dev is None else dev,
                    "isBest?": "" if is_best is None else is_best,
                })
        print(f"relatório: {out}  ({len(by_group[grupo])} instâncias)")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_solver_args(a):
    args = ["--alg", a.alg, "--shake", a.shake, "--seed", str(a.seed)]
    if a.alpha is not None:
        args += ["--alpha", str(a.alpha)]
    if a.kmax is not None:
        args += ["--kmax", str(a.kmax)]
    if a.iters is not None:
        args += ["--iters", str(a.iters)]
    if a.no_improve is not None:
        args += ["--no-improve", str(a.no_improve)]
    return args


def main(argv=None):
    pa = argparse.ArgumentParser(description="Runner de benchmark do IpMU (retomável).")
    pa.add_argument("--instances", default=str(REPO / "instances"),
                    help="pasta raiz das instâncias (recursivo). Padrão: instances/")
    pa.add_argument("--exe", default=str(REPO / "ipmu.exe"), help="caminho do ipmu.exe")
    pa.add_argument("--raw", default=None,
                    help="checkpoint CSV. Padrão: results/raw/<alg>_seed<seed>.csv")
    pa.add_argument("--sota", default=str(REPO / "results" / "ResultsInstanceByInstance.xlsx"),
                    help="planilha de referência do artigo (coluna SOTA)")
    pa.add_argument("--report-dir", default=str(REPO / "results" / "report"))
    pa.add_argument("--report-only", action="store_true",
                    help="apenas (re)gera o relatório a partir do checkpoint")
    pa.add_argument("--tol", type=float, default=1e-6, help="tolerância de isBest?")
    # Passthrough para o solver.
    pa.add_argument("--alg", default="bvns", choices=["bvns", "rvns"])
    pa.add_argument("--shake", default="random", choices=["random", "greedy"])
    pa.add_argument("--alpha", type=float, default=None)
    pa.add_argument("--kmax", type=int, default=None)
    pa.add_argument("--iters", type=int, default=None)
    pa.add_argument("--no-improve", dest="no_improve", type=int, default=None)
    pa.add_argument("--seed", type=int, default=42)
    a = pa.parse_args(argv)

    raw_path = Path(a.raw) if a.raw else (
        REPO / "results" / "raw" / f"{a.alg}_seed{a.seed}.csv")
    report_dir = Path(a.report_dir)
    tag = f"{a.alg}_seed{a.seed}"
    sota = load_sota(Path(a.sota))
    print(f"SOTA: {len(sota)} instâncias de referência carregadas de {a.sota}")

    if a.report_only:
        build_report(raw_path, sota, report_dir, tag, a.tol)
        return 0

    exe = Path(a.exe)
    if not exe.exists():
        print(f"erro: ipmu.exe não encontrado em {exe}. Rode .\\build.ps1 antes.",
              file=sys.stderr)
        return 1

    instances = enumerate_instances(Path(a.instances))
    done = load_done(raw_path)
    pending = [(f, info) for (f, info) in instances
               if os.path.relpath(f, REPO) not in done]
    print(f"instâncias: {len(instances)} totais | {len(done)} já feitas | "
          f"{len(pending)} pendentes")

    solver_args = build_solver_args(a)
    fh, writer = open_raw_writer(raw_path)
    failures = raw_path.with_name(raw_path.stem + "_failures.log")

    processed = 0
    try:
        for f, (base, n, m, p, B, idx) in pending:
            rel = os.path.relpath(f, REPO)
            t0 = time.time()
            try:
                obj, tempo_s = run_solver(exe, f, solver_args)
            except Exception as e:  # falha → registra e segue (retomada tenta de novo)
                with failures.open("a", encoding="utf-8") as ff:
                    ff.write(f"{rel}\t{e}\n")
                print(f"  FALHA {rel}: {e}", file=sys.stderr)
                continue
            writer.writerow({
                "instancia_rel": rel, "basename": base, "grupo": n,
                "p": p, "B": B, "alg": a.alg, "seed": a.seed,
                "objetivo": repr(obj), "tempo_s": repr(tempo_s),
            })
            fh.flush()
            os.fsync(fh.fileno())  # garante persistência por instância
            processed += 1
            print(f"  [{processed}/{len(pending)}] {base}  f={obj:.4f}  "
                  f"t={tempo_s:.3f}s  (lote {time.time() - t0:.2f}s)")
    except KeyboardInterrupt:
        print("\ninterrompido — checkpoint preservado; rode de novo para continuar.")
    finally:
        fh.close()

    build_report(raw_path, sota, report_dir, tag, a.tol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

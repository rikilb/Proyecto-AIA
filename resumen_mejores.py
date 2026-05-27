import argparse
from pathlib import Path
import unicodedata


def normalize(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    ).lower()


def parse_best_blocks(text: str, dataset_default: str, mode: str):
    best = {}
    order = []
    dataset = dataset_default
    in_best = False
    params = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        norm = normalize(line)

        if norm.startswith("dataset:"):
            dataset = line.split(":", 1)[1].strip() or dataset_default
            if dataset not in order:
                order.append(dataset)
            continue

        if norm.startswith("mejor combinacion"):
            in_best = True
            params = None
            continue

        if in_best and norm.startswith("params"):
            params = line.split(":", 1)[1].strip()
            continue

        if in_best and norm.startswith("rendimiento validacion"):
            value_str = line.split(":", 1)[1].strip()
            try:
                val = float(value_str)
            except ValueError:
                in_best = False
                continue

            if dataset not in order:
                order.append(dataset)

            if mode == "todas":
                best.setdefault(dataset, []).append({"params": params, "val": val})
            elif mode == "ultimo":
                best[dataset] = [{"params": params, "val": val}]
            else:
                prev = best.get(dataset, [])
                if not prev or val > prev[0]["val"]:
                    best[dataset] = [{"params": params, "val": val}]

            in_best = False

    return best, order


def write_summary(best, order, out_path, skip_default, dataset_default):
    lines = []
    for dataset in order:
        if skip_default and dataset == dataset_default:
            continue
        entries = best.get(dataset, [])
        if not entries:
            continue
        lines.append(f"DATASET: {dataset}")
        for i, entry in enumerate(entries, start=1):
            lines.append(f"  Mejor {i}:")
            lines.append(f"    Params: {entry['params']}")
            lines.append(f"    Rendimiento validacion: {entry['val']:.4f}")
        lines.append("")
    Path(out_path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="resultados_hiperparametros_log")
    parser.add_argument("--out", default="resumen_mejores.txt")
    parser.add_argument("--modo", choices=["mejor", "ultimo", "todas"], default="todas")
    parser.add_argument("--default-dataset", default="SIN_DATASET")
    parser.add_argument("--skip-default", action="store_true")
    args = parser.parse_args()

    text = Path(args.log).read_text(encoding="utf-8")
    best, order = parse_best_blocks(text, args.default_dataset, args.modo)
    write_summary(best, order, args.out, args.skip_default, args.default_dataset)


if __name__ == "__main__":
    main()
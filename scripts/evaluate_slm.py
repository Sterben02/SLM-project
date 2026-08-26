# scripts/evaluate_slm.py
"""Оценка SLM-детектора на test-датасете + сравнение с baseline."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.models import CodeChunk, DatasetItem
from scanner.llm import SLMDetector


def load_dataset(path):
    with open(path, encoding="utf-8") as f:
        return [DatasetItem(**json.loads(l)) for l in f if l.strip()]


def item_to_chunk(item):
    return CodeChunk(
        file_path=item.file_path, language=item.language,
        start_line=item.line_number, end_line=item.line_number,
        target_snippet=item.target_snippet,
        context_before=item.context_before, context_after=item.context_after,
    )


def get_actual_class(item):
    if item.labels.is_secret:
        return f"secret_{item.labels.secret_type}"
    if item.labels.is_insecure:
        return f"insecure_{item.labels.insecure_type}"
    return "negative"


def main():
    test_path = sys.argv[1] if len(sys.argv) > 1 else "data/test.jsonl"
    print("=" * 70)
    print("🤖 ОЦЕНКА SLM-ДЕТЕКТОРА")
    print(f"Датасет: {test_path}")
    print("⏱  Ожидание: 15-25 минут (527 примеров × 1-3 сек на CPU)")
    print("=" * 70)

    items = load_dataset(test_path)
    print(f"Загружено примеров: {len(items)}")

    detector = SLMDetector()

    tp = fp = fn = tn = 0
    errors = 0
    total_time = 0.0

    for i, item in enumerate(items):
        chunk = item_to_chunk(item)
        actual_positive = get_actual_class(item) != "negative"

        start = time.perf_counter()
        try:
            findings = detector.detect(chunk)
        except Exception as e:
            errors += 1
            findings = []
        total_time += time.perf_counter() - start

        predicted_positive = len(findings) > 0

        if actual_positive and predicted_positive:
            tp += 1
        elif not actual_positive and predicted_positive:
            fp += 1
        elif actual_positive and not predicted_positive:
            fn += 1
        else:
            tn += 1

        if (i + 1) % 25 == 0 or i == 0:
            elapsed = total_time
            remaining = (elapsed / (i + 1)) * (len(items) - i - 1)
            print(f"  ⏳ {i+1:3}/{len(items)} | TP={tp:3} FP={fp:3} FN={fn:3} TN={tn:3} | "
                  f"~{remaining/60:.1f} мин осталось")

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    print("\n" + "=" * 70)
    print("📈 МЕТРИКИ SLM:")
    print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}  (errors={errors})")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1:        {f1:.4f}")
    print(f"  FPR:       {fpr:.4f}  ← главная метрика")
    print(f"  FNR:       {fnr:.4f}")
    print(f"  Время/пример: {total_time/len(items)*1000:.0f} мс")
    print("=" * 70)

    results = {
        "dataset": test_path, "total": len(items), "errors": errors,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
    }
    Path("reports").mkdir(exist_ok=True)
    with open("reports/slm_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("💾 Сохранено: reports/slm_metrics.json")

    # СРАВНЕНИЕ С BASELINE
    bp = Path("reports/baseline_metrics.json")
    if bp.exists():
        b = json.loads(bp.read_text(encoding="utf-8"))["binary"]
        print("\n" + "=" * 70)
        print("🆚 BASELINE vs SLM (главная гипотеза проекта):")
        print(f"  {'Метрика':<12}{'Baseline':>10}{'SLM':>10}{'Изменение':>12}")
        print(f"  {'Precision':<12}{b['precision']:>10.4f}{precision:>10.4f}{precision-b['precision']:>+12.4f}")
        print(f"  {'Recall':<12}{b['recall']:>10.4f}{recall:>10.4f}{recall-b['recall']:>+12.4f}")
        print(f"  {'F1':<12}{b['f1']:>10.4f}{f1:>10.4f}{f1-b['f1']:>+12.4f}")
        print(f"  {'FPR':<12}{b['fpr']:>10.4f}{fpr:>10.4f}{fpr-b['fpr']:>+12.4f}")
        print(f"  {'FNR':<12}{b['fnr']:>10.4f}{fnr:>10.4f}{fnr-b['fnr']:>+12.4f}")
        print("=" * 70)

        if fpr < b["fpr"] and recall >= b["recall"] * 0.9:
            print("🎉 ГИПОТЕЗА ПОДТВЕРЖДЕНА: SLM снизила FPR при сохранении recall!")
        elif fpr < b["fpr"]:
            print("✅ SLM снизила FPR, но recall просел")
        else:
            print("⚠️  SLM не снизила FPR — нужен анализ")


if __name__ == "__main__":
    main()
# scripts/evaluate_baseline.py
"""
Оценка baseline-детекторов на тестовом датасете.
Все метрики из ТЗ:
1. Precision
2. Recall
3. F1-score
4. False Positive Rate
5. False Negative Rate
6. Macro-F1 по классам
7. Среднее время анализа одного примера
"""
import json
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.models import CodeChunk, DatasetItem
from scanner.detectors import get_baseline_detectors


def load_dataset(path: str) -> list:
    if not Path(path).exists():
        print(f"Файл не найден: {path}")
        sys.exit(1)
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(DatasetItem(**json.loads(line)))
    return items


def item_to_chunk(item: DatasetItem) -> CodeChunk:
    return CodeChunk(
        file_path=item.file_path,
        language=item.language,
        start_line=item.line_number,
        end_line=item.line_number,
        target_snippet=item.target_snippet,
        context_before=item.context_before,
        context_after=item.context_after,
    )


def get_actual_class(item: DatasetItem) -> str:
    """Истинный класс примера."""
    if item.labels.is_secret:
        return f"secret_{item.labels.secret_type}"
    if item.labels.is_insecure:
        # Для insecure_code используем как есть
        if item.labels.insecure_type == "insecure_code":
            return "insecure_insecure_code"
        return f"insecure_{item.labels.insecure_type}"
    return "negative"


def finding_to_class(finding) -> str:
    """Маппинг типа finding на наши классы."""
    t = finding.type

    if finding.category == "secret":
        if t in ("api_key", "aws_access_key", "generic_api_key", "hardcoded_api_key"):
            return "secret_api_key"
        if t in ("access_token", "github_token", "hardcoded_access_token"):
            return "secret_access_token"
        if t in ("password", "password_in_code", "hardcoded_password"):
            return "secret_password"
        if t in ("private_key", "hardcoded_private_key"):
            return "secret_private_key"
        if t in ("jwt", "jwt_token", "hardcoded_jwt"):
            return "secret_jwt"
        if t == "high_entropy_string":
            return "secret_api_key"
        return "secret_unknown"
    else:
        mapping = {
            "eval_usage": "insecure_eval_usage",
            "exec_usage": "insecure_exec_usage",
            "shell_true": "insecure_shell_true",
            "os_system": "insecure_shell_true",
            "sql_concat": "insecure_sql_concat",
            "sql_fstring": "insecure_sql_concat",
            "sql_percent": "insecure_sql_concat",
            "weak_hash_md5": "insecure_weak_hash",
            "weak_hash_sha1": "insecure_weak_hash",
            "hardcoded_creds": "insecure_hardcoded_creds",
            "hardcoded_creds_dict": "insecure_hardcoded_creds",
            # ДОБАВЛЕНО: для общего класса
            "insecure_code": "insecure_insecure_code",
        }
        return mapping.get(t, "insecure_other")


def main():
    test_path = sys.argv[1] if len(sys.argv) > 1 else "data/test.jsonl"

    print("=" * 70)
    print("ОЦЕНКА BASELINE-ДЕТЕКТОРОВ")
    print(f"Датасет: {test_path}")
    print("=" * 70)

    items = load_dataset(test_path)
    detectors = get_baseline_detectors()
    print(f"Примеров: {len(items)}")
    print(f"Детекторы: {[d.name for d in detectors]}\n")

    # ===== Бинарная классификация (есть срабатывание / нет) =====
    tp = fp = fn = tn = 0
    total_time = 0.0

    # ===== Мультикласс (для Macro-F1) =====
    class_tp = defaultdict(int)
    class_fp = defaultdict(int)
    class_fn = defaultdict(int)

    all_classes = set()

    for item in items:
        chunk = item_to_chunk(item)
        actual = get_actual_class(item)
        all_classes.add(actual)

        actual_positive = actual != "negative"

        # Замер времени
        start = time.perf_counter()
        findings = []
        for detector in detectors:
            findings.extend(detector.detect(chunk))
        total_time += time.perf_counter() - start

        predicted_positive = len(findings) > 0

        # Бинарные метрики
        if actual_positive and predicted_positive:
            tp += 1
        elif not actual_positive and predicted_positive:
            fp += 1
        elif actual_positive and not predicted_positive:
            fn += 1
        else:
            tn += 1

        # Мультикласс: предсказанный класс = класс finding с макс. confidence
        if findings:
            best = max(findings, key=lambda f: f.confidence)
            predicted = finding_to_class(best)
        else:
            predicted = "negative"

        all_classes.add(predicted)

        if predicted == actual:
            class_tp[actual] += 1
        else:
            class_fp[predicted] += 1
            class_fn[actual] += 1

    # ===== Бинарные метрики =====
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0
    avg_time = total_time / len(items) if items else 0

    print("БИНАРНЫЕ МЕТРИКИ (secret/insecure vs negative):")
    print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"  1. Precision:        {precision:.4f}")
    print(f"  2. Recall:           {recall:.4f}")
    print(f"  3. F1-score:         {f1:.4f}")
    print(f"  4. FPR:              {fpr:.4f}")
    print(f"  5. FNR:              {fnr:.4f}")
    print(f"  7. Ср. время/пример: {avg_time * 1000:.2f} мс")

    # ===== Macro-F1 по классам =====
    print("\nМЕТРИКИ ПО КЛАССАМ (one-vs-rest):")
    print(f"  {'Класс':<28}{'Prec':>7}{'Rec':>7}{'F1':>7}")
    print("  " + "-" * 50)

    f1_scores = []
    for cls in sorted(all_classes):
        tp_c = class_tp[cls]
        fp_c = class_fp[cls]
        fn_c = class_fn[cls]

        prec_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) else 0
        rec_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) else 0
        f1_c = 2 * prec_c * rec_c / (prec_c + rec_c) if (prec_c + rec_c) else 0

        f1_scores.append(f1_c)
        print(f"  {cls:<28}{prec_c:>7.3f}{rec_c:>7.3f}{f1_c:>7.3f}")

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0
    print(f"\n  6. Macro-F1:         {macro_f1:.4f}")

    # ===== Сохранение результатов =====
    results = {
        "dataset": test_path,
        "total_examples": len(items),
        "binary": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
        },
        "macro_f1": round(macro_f1, 4),
        "avg_time_ms": round(avg_time * 1000, 2),
    }

    Path("reports").mkdir(exist_ok=True)
    with open("reports/baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nСохранено: reports/baseline_metrics.json")


if __name__ == "__main__":
    main()
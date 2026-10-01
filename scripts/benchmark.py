"""
DataGuard 2.0 Empirical Performance Benchmark
Runs reproducible, truthful benchmarks measuring:
1. Pure Python Ingestion Throughput (Pandas-free)
2. Statistical & Vectorized ML Profiling Throughput
3. Statistical Outlier Detection (Z-score, IQR)
4. Vectorized Isolation Forest ML Detector
5. Full End-to-End Multi-Agent Swarm Audit (Inspector, Drift, RCA, Recommendation, Cryptographic HMAC)
6. Peak Memory Footprint (tracemalloc)
"""

import sys
import os
import time
import tracemalloc
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.etl.extractor.dataset_loader import DatasetLoader
from app.ml.profiler import DatasetProfiler
from app.ml.statistical_detector import StatisticalAnomalyDetector
from app.ml.isolation_forest import IsolationForestDetector
from app.agents.orchestrator import MultiAgentOrchestrator


def benchmark_dataset(rel_path: str, max_rows: int | None = None) -> dict:
    print(f"\n{'='*70}")
    print(f"BENCHMARKING DATASET: {rel_path} (max_rows={max_rows or 'ALL'})")
    print(f"{'='*70}")

    # 1. Ingestion Benchmark
    tracemalloc.start()
    t0 = time.perf_counter()
    rows = DatasetLoader.load_dataset(rel_path)
    if max_rows and len(rows) > max_rows:
        rows = rows[:max_rows]
    t_ingest = time.perf_counter() - t0
    current_mem, peak_mem_ingest = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    row_count = len(rows)
    col_count = len(rows[0]) if rows else 0
    ingest_throughput = row_count / t_ingest if t_ingest > 0 else 0.0

    print(f"  [1] Ingestion: {row_count:,} rows, {col_count} columns in {t_ingest:.3f}s ({ingest_throughput:,.1f} rows/s)")
    print(f"      Peak Memory: {peak_mem_ingest / (1024 * 1024):.2f} MB")

    # 2. Profiling Benchmark
    tracemalloc.start()
    t0 = time.perf_counter()
    profile = DatasetProfiler.profile(rows)
    t_profile = time.perf_counter() - t0
    _, peak_mem_profile = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    profile_throughput = row_count / t_profile if t_profile > 0 else 0.0
    print(f"  [2] Profiling: {row_count:,} rows profiled in {t_profile:.3f}s ({profile_throughput:,.1f} rows/s)")

    # 3. Statistical Anomaly Detection
    stat_detector = StatisticalAnomalyDetector()
    t0 = time.perf_counter()
    stat_findings = stat_detector.detect_outliers(rows)
    t_stat = time.perf_counter() - t0
    stat_throughput = row_count / t_stat if t_stat > 0 else 0.0
    print(f"  [3] Statistical Detector: {len(stat_findings.get('findings', []))} findings in {t_stat:.3f}s ({stat_throughput:,.1f} rows/s)")

    # 4. Vectorized Isolation Forest ML Detector
    iso_detector = IsolationForestDetector()
    t0 = time.perf_counter()
    iso_findings = iso_detector.detect(rows)
    t_iso = time.perf_counter() - t0
    iso_throughput = row_count / t_iso if t_iso > 0 else 0.0
    print(f"  [4] Isolation Forest ML: {len(iso_findings.get('findings', []))} findings in {t_iso:.3f}s ({iso_throughput:,.1f} rows/s)")

    # 5. Full Multi-Agent Swarm Audit (Inspector, Drift, RCA, Recommendation, Cryptographic HMAC)
    orchestrator = MultiAgentOrchestrator()
    tracemalloc.start()
    t0 = time.perf_counter()
    audit_dossier = orchestrator.audit_dataset(
        rows=rows,
        dataset_path=rel_path,
        generate_reports=False,
    )
    t_swarm = time.perf_counter() - t0
    _, peak_mem_swarm = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    swarm_throughput = row_count / t_swarm if t_swarm > 0 else 0.0
    total_findings = len(audit_dossier.get("findings", []))
    audit_hash = audit_dossier.get("audit_hash", "N/A")

    print(f"  [5] Multi-Agent Swarm Audit: {total_findings} findings, signed HMAC {audit_hash[:16]}... in {t_swarm:.3f}s ({swarm_throughput:,.1f} rows/s)")

    total_processing_time = t_ingest + t_swarm
    total_pipeline_throughput = row_count / total_processing_time if total_processing_time > 0 else 0.0

    print(f"  ------------------------------------------------------------------")
    print(f"  TOTAL END-TO-END PIPELINE TIME (Ingest + Full Swarm): {total_processing_time:.3f}s")
    print(f"  EFFECTIVE END-TO-END THROUGHPUT: {total_pipeline_throughput:,.1f} rows/s")
    print(f"  OVERALL PEAK HEAP MEMORY: {max(peak_mem_ingest, peak_mem_profile, peak_mem_swarm) / (1024 * 1024):.2f} MB")

    return {
        "dataset": rel_path,
        "rows": row_count,
        "columns": col_count,
        "ingest_time_s": round(t_ingest, 4),
        "ingest_throughput_rows_per_s": round(ingest_throughput, 1),
        "profile_time_s": round(t_profile, 4),
        "profile_throughput_rows_per_s": round(profile_throughput, 1),
        "stat_time_s": round(t_stat, 4),
        "iso_time_s": round(t_iso, 4),
        "swarm_audit_time_s": round(t_swarm, 4),
        "swarm_throughput_rows_per_s": round(swarm_throughput, 1),
        "total_time_s": round(total_processing_time, 4),
        "effective_throughput_rows_per_s": round(total_pipeline_throughput, 1),
        "peak_memory_mb": round(max(peak_mem_ingest, peak_mem_profile, peak_mem_swarm) / (1024 * 1024), 2),
        "findings_detected": total_findings,
        "audit_hash": audit_hash,
    }


def main():
    print("=" * 70)
    print("DATAGUARD 2.0 PERFORMANCE & INTEGRITY BENCHMARK SUITE")
    print("Running on Python 3.12 without Pandas")
    print("=" * 70)

    datasets = [
        ("olist/olist_customers_dataset.csv", 20000),
        ("olist/olist_customers_dataset.csv", None),
        ("olist/olist_order_items_dataset.csv", None),
    ]

    results = []
    for rel_path, max_rows in datasets:
        try:
            res = benchmark_dataset(rel_path, max_rows)
            results.append(res)
        except Exception as e:
            print(f"Failed benchmark for {rel_path}: {e}")
            import traceback
            traceback.print_exc()

    out_file = Path(__file__).resolve().parent / "benchmark_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY BENCHMARK RESULTS (MEASURED EMPIRICAL DATA)")
    print("=" * 70)
    print(f"{'Dataset':<35} | {'Rows':<8} | {'Total (s)':<10} | {'Throughput':<15} | {'Peak Mem':<10}")
    print("-" * 88)
    for r in results:
        print(f"{r['dataset']:<35} | {r['rows']:<8} | {r['total_time_s']:<10.2f} | {r['effective_throughput_rows_per_s']:>10,.1f} r/s | {r['peak_memory_mb']:>7.2f} MB")
    print("=" * 70)
    print(f"Results saved to {out_file}")


if __name__ == "__main__":
    main()

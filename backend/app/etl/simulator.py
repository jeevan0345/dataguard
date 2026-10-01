"""
DataGuard ETL Pipeline Fault-Injection Simulator
Simulates enterprise ETL pipeline runs with controllable anomaly injections for live demonstrations.
"""

import copy
import random
from typing import Any
from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.agents.orchestrator import MultiAgentOrchestrator


class ETLSimulator:
    """
    Executes simulated ETL pipeline workloads with selectable failure modes.
    """

    @staticmethod
    def run_simulation(
        dataset_path: str = "olist/olist_orders_dataset.csv",
        mode: str = "CLEAN",
        sample_size: int = 500,
    ) -> dict[str, Any]:
        """
        Loads a sample from real data, injects selected fault mode,
        and runs the complete DataGuard multi-agent swarm.

        Modes:
        - CLEAN: Baseline run with no injected anomalies.
        - MISSING_VALUES: Injects nulls in critical columns.
        - DUPLICATES: Injects duplicated rows.
        - SCHEMA_DRIFT: Mutates expected schema (deletes column, adds column).
        - ML_OUTLIERS: Injects extreme numeric spikes.
        - DISASTER: Multi-fault composite corruption.
        """
        all_rows = DatasetLoader.load_dataset(dataset_path)
        if not all_rows:
            raise ValueError(f"Failed to load dataset at {dataset_path}")

        # Take reproducible sample from pristine rows for deterministic baseline behavior
        clean_candidates = [
            r for r in all_rows
            if not any(v is None or str(v).strip() == "" for v in r.values())
        ]
        source_pool = clean_candidates if len(clean_candidates) >= sample_size else all_rows
        sample_rows = [copy.deepcopy(r) for r in source_pool[:sample_size]]

        actual_schema = SchemaInference.infer_schema(sample_rows)
        expected_schema = copy.deepcopy(actual_schema)

        injected_faults = []

        if mode == "MISSING_VALUES" or mode == "DISASTER":
            # Inject nulls into second column (20% nulls)
            target_col = list(sample_rows[0].keys())[1]
            for i in range(0, len(sample_rows), 5):
                sample_rows[i][target_col] = None
            injected_faults.append(f"Injected 20% missing values in column '{target_col}'")

        if mode == "DUPLICATES" or mode == "DISASTER":
            # Duplicate first 25 rows
            dups = [copy.deepcopy(r) for r in sample_rows[:25]]
            sample_rows.extend(dups)
            injected_faults.append(f"Injected 25 duplicate rows ({len(dups)} duplicates)")

        if mode == "SCHEMA_DRIFT" or mode == "DISASTER":
            # Remove a column from actual data
            col_to_remove = list(sample_rows[0].keys())[-1]
            for r in sample_rows:
                r.pop(col_to_remove, None)
            injected_faults.append(f"Removed expected column '{col_to_remove}' from pipeline output")

        if mode == "ML_OUTLIERS" or mode == "DISASTER":
            # Find a non-ID numeric column or inject a numeric feature if none exists
            target_numeric = None
            for col, dtype in actual_schema.items():
                if dtype in ["integer", "float"] and not (col.endswith("_id") or col == "id"):
                    target_numeric = col
                    break
            if not target_numeric:
                target_numeric = "freight_value"
                for r in sample_rows:
                    r[target_numeric] = 15.50
                actual_schema[target_numeric] = "float"
                expected_schema[target_numeric] = "float"

            for i in range(5):
                sample_rows[i][target_numeric] = 999999.99
            injected_faults.append(f"Injected extreme numerical outliers in column '{target_numeric}'")

        # Run MultiAgentOrchestrator
        orchestrator = MultiAgentOrchestrator()
        audit_result = orchestrator.audit_dataset(
            rows=sample_rows,
            expected_schema=expected_schema,
            actual_schema=SchemaInference.infer_schema(sample_rows),
            dataset_path=dataset_path,
            generate_reports=True,
        )

        return {
            "simulation_mode": mode,
            "sample_size": sample_size,
            "injected_faults": injected_faults,
            "final_row_count": len(sample_rows),
            "audit": audit_result,
        }

"""Compliance, Exceptions & Ground Truth Evaluation API Endpoints."""

import os
import csv
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.schemas import ComplianceViolationItem
from backend.app.services.compliance import scan_compliance_violations

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


@router.get("/issues", response_model=List[ComplianceViolationItem])
def list_compliance_issues(db: Session = Depends(get_db)):
    """Run real-time compliance scan across database to detect policy breaches and anomalies."""
    return scan_compliance_violations(db)


@router.get("/benchmark")
def evaluate_ground_truth_benchmark(db: Session = Depends(get_db)):
    """Benchmark detected compliance anomalies against isolated ground truth.

    Computes:
      - Precision: TP / (TP + FP)
      - Recall: TP / (TP + FN)
      - F1 Score
    """
    gt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "data",
        "ground_truth",
        "ground_truth.csv",
    )

    if not os.path.exists(gt_path):
        return {"error": "ground_truth.csv not found", "detected_count": 0}

    # Load ground truth
    ground_truth_ids = set()
    with open(gt_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth_ids.add(row["record_id"])

    # Run detection
    detected = scan_compliance_violations(db)
    detected_ids = {item["record_id"] for item in detected}

    true_positives = len(detected_ids.intersection(ground_truth_ids))
    false_positives = len(detected_ids - ground_truth_ids)
    false_negatives = len(ground_truth_ids - detected_ids)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0

    return {
        "ground_truth_total": len(ground_truth_ids),
        "detected_total": len(detected_ids),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "evaluation_summary": (
            f"Evaluated {len(ground_truth_ids)} isolated ground truth anomalies with "
            f"F1-Score: {f1_score * 100:.1f}%, Precision: {precision * 100:.1f}%, Recall: {recall * 100:.1f}%."
        ),
    }


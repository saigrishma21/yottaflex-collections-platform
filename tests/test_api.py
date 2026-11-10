"""Unit and integration tests for API endpoints and controllers."""

import pytest
from backend.app.database import SessionLocal
from backend.app.main import health_check
from backend.app.routes.dashboard import get_dashboard_summary, get_dashboard_chart_metrics, list_promises
from backend.app.routes.collections import list_cases, get_priority_worklist, get_case_detail
from backend.app.routes.compliance import list_compliance_issues, evaluate_ground_truth_benchmark
from backend.app.routes.customers import list_customers, get_customer
from backend.app.routes.loans import list_loans, get_loan, get_loan_installments


@pytest.fixture(scope="module")
def db():
    """Database session fixture."""
    session = SessionLocal()
    yield session
    session.close()


def test_health_check_endpoint():
    """Verify health check returns valid service info."""
    data = health_check()
    assert data["status"] == "ONLINE"
    assert "version" in data
    assert len(data["features"]) > 0


def test_dashboard_summary_endpoint(db):
    """Verify portfolio summary metrics."""
    res = get_dashboard_summary(db=db)
    assert res["total_customers"] > 0
    assert res["total_loans"] > 0
    assert res["active_cases_count"] > 0
    assert res["compliance_issues_count"] > 0


def test_dashboard_metrics_endpoint(db):
    """Verify charts metrics."""
    res = get_dashboard_chart_metrics(db=db)
    assert "delinquency_buckets" in res
    assert "priority_distribution" in res
    assert "loan_status_distribution" in res


def test_list_collections_endpoint(db):
    """Verify paginated collection cases."""
    cases = list_cases(skip=0, limit=10, db=db)
    assert len(cases) > 0
    assert hasattr(cases[0], "case_id")
    assert hasattr(cases[0], "priority_score")


def test_priority_worklist_endpoint(db):
    """Verify priority worklist ordering."""
    worklist = get_priority_worklist(limit=5, db=db)
    assert len(worklist) > 0
    # First item should have high or critical priority score
    assert worklist[0].priority_score >= 50.0


def test_case_detail_endpoint(db):
    """Verify 360 case detail retrieval."""
    worklist = get_priority_worklist(limit=1, db=db)
    case_id = worklist[0].case_id
    detail = get_case_detail(case_id=case_id, db=db)
    assert detail["case"].case_id == case_id
    assert detail["customer"] is not None
    assert detail["loan"] is not None
    assert "score_explanation" in detail


def test_compliance_scanner_endpoint(db):
    """Verify compliance scanner returns all detected issues."""
    issues = list_compliance_issues(db=db)
    assert len(issues) > 0
    violation_codes = {i["violation_code"] for i in issues}
    assert "ERR_PAID_IN_COLLECTION" in violation_codes
    assert "ERR_OUTSIDE_CONTACT_WINDOW" in violation_codes
    assert "ERR_WRONG_PAYMENT_ALLOCATION" in violation_codes
    assert "ERR_PROMISE_EXCEEDS_ARREARS" in violation_codes
    assert "ERR_DISPUTED_TREATED_CONFIRMED" in violation_codes


def test_compliance_ground_truth_benchmark(db):
    """Verify benchmark achieves 100% precision and recall against isolated ground truth."""
    benchmark = evaluate_ground_truth_benchmark(db=db)
    assert benchmark["ground_truth_total"] > 0
    assert benchmark["detected_total"] == benchmark["ground_truth_total"]
    assert benchmark["precision"] == 1.0
    assert benchmark["recall"] == 1.0
    assert benchmark["f1_score"] == 1.0


def test_list_customers_and_loans(db):
    """Verify customer and loan list queries."""
    custs = list_customers(skip=0, limit=5, db=db)
    assert len(custs) == 5
    loans = list_loans(skip=0, limit=5, db=db)
    assert len(loans) == 5
    insts = get_loan_installments(loan_id=loans[0].loan_id, db=db)
    assert len(insts) > 0

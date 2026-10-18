from typing import Any, Dict, List, Optional

from app.demo_data import PROPERTIES


def list_properties() -> List[Dict[str, Any]]:
    return PROPERTIES


def get_property_by_id(property_id: str) -> Optional[Dict[str, Any]]:
    for property_item in PROPERTIES:
        if property_item["id"] == property_id:
            return property_item
    return None


def get_purchase_checklist(property_id: str) -> Optional[Dict[str, Any]]:
    property_item = get_property_by_id(property_id)
    if not property_item:
        return None

    checklist = [
        {
            "id": "identity",
            "title": "Confirm seller identity and deed holder",
            "status": "in_progress",
            "detail": "Compare current seller identity with the deed holder and any mutation record.",
            "urgency": "High",
        },
        {
            "id": "mutation",
            "title": "Review mutation history and ownership transfer",
            "status": "pending",
            "detail": "Check for missing or incomplete document chain before any payment commitment.",
            "urgency": "High",
        },
        {
            "id": "documents",
            "title": "Validate tax, khatian, and agreement records",
            "status": "done",
            "detail": "Cross-check title deed, tax receipt, and khatian details for discrepancies.",
            "urgency": "Medium",
        },
        {
            "id": "risk",
            "title": "Assess dispute, encumbrance, and case screening",
            "status": "pending",
            "detail": "Review whether the plot has unresolved dispute or acquisition-related concerns.",
            "urgency": "High",
        },
        {
            "id": "legal",
            "title": "Arrange official verification before final registration",
            "status": "pending",
            "detail": "Do not treat this summary as a legal guarantee; seek a registered professional review.",
            "urgency": "Critical",
        },
    ]

    if property_item["risk_level"] == "No issue identified in available checks":
        checklist[0]["status"] = "done"
        checklist[1]["status"] = "done"
        checklist[3]["status"] = "done"

    completed = sum(1 for step in checklist if step["status"] == "done")
    total = len(checklist)

    return {
        "property_id": property_item["id"],
        "title": property_item["title"],
        "overall_status": "Buyer caution required" if completed < total else "Ready for professional verification",
        "progress": round((completed / total) * 100),
        "checklist": checklist,
    }


def get_moderation_queue() -> Dict[str, List[Dict[str, Any]]]:
    queue = [
        {
            "id": "MOD-201",
            "property_id": "LG-1002",
            "title": "Green Valley Parcel",
            "status": "Under review",
            "priority": "High",
            "reason": "Ownership chain gap and dispute check flagged.",
            "reviewer": "Admin Team",
            "updated_at": "2026-10-15 09:20",
        },
        {
            "id": "MOD-202",
            "property_id": "LG-1001",
            "title": "North View Land Plot",
            "status": "Awaiting evidence",
            "priority": "Critical",
            "reason": "Name mismatch and missing mutation record.",
            "reviewer": "Compliance Desk",
            "updated_at": "2026-10-15 08:45",
        },
        {
            "id": "MOD-203",
            "property_id": "LG-1003",
            "title": "River Edge Plot",
            "status": "Approved for manual check",
            "priority": "Medium",
            "reason": "Low-risk documents but final mutation confirmation pending.",
            "reviewer": "Field Office",
            "updated_at": "2026-10-15 07:50",
        },
    ]
    return {"queue": queue}


def get_dashboard_summary(user_id=None) -> Dict[str, int]:
    """Return account-scoped REAL demo activity, never invented engagement counters.

    A successful local analysis only means text was read, NOT that a deed was
    authenticated or that any government record was consulted.
    """
    if not user_id:
        return {key: 0 for key in (
            'total_properties_viewed','saved_properties','demo_documents',
            'verification_requests','completed_checks','pending_checks',
            'unresolved_issues','missing_documents','upcoming_actions',
            'recent_alerts','simulated_purchase_requests')}
    from app.database import connect
    with connect() as db:
        demo_checks = db.execute('SELECT COUNT(*) FROM registry_checks WHERE user_id=?', (user_id,)).fetchone()[0]
        doc_count = db.execute('SELECT COUNT(*) FROM private_documents WHERE owner_user_id=?', (user_id,)).fetchone()[0]
        extraction_count = db.execute('SELECT COUNT(*) FROM verification_events WHERE user_id=?', (user_id,)).fetchone()[0]
        analyzed_count = db.execute("""SELECT COUNT(*) FROM verification_events
            WHERE user_id=? AND evidence_status IN ('success','partial')""", (user_id,)).fetchone()[0]
        unreadable_count = db.execute("""SELECT COUNT(*) FROM verification_events
            WHERE user_id=? AND evidence_status='unreadable'""", (user_id,)).fetchone()[0]
        mismatched_checks = db.execute("""SELECT COUNT(*) FROM registry_checks
            WHERE user_id=? AND result IN ('demo_mismatch','incomplete_demo_check','insufficient_data')""", (user_id,)).fetchone()[0]
    return {
        'total_properties_viewed': 0, 'saved_properties': 0, 'demo_documents': doc_count,
        'verification_requests': demo_checks + extraction_count,
        'completed_checks': demo_checks + analyzed_count,
        'pending_checks': unreadable_count,
        'unresolved_issues': mismatched_checks + unreadable_count,
        'missing_documents': 0, 'upcoming_actions': 0,
        'recent_alerts': 0, 'simulated_purchase_requests': 0,
    }

from __future__ import annotations
import os
from collections import defaultdict
from typing import Dict, List, Set, TypedDict, Optional, cast

from app.services.report_row import ReportRow


class CustomerPacket(TypedDict):
    """
    A single customer's packet used downstream for PDFs and emails.
    """
    customer_id: str
    customer_name: str
    project_ids: List[str]
    recipients: List[str]
    rows: List[ReportRow]


def group_rows_by_customer_id(rows: List[ReportRow]) -> Dict[str, CustomerPacket]:
    """
    Group all report rows by customer_id and collect the involved project_ids.

    Returns:
        Dict keyed by customer_id. Each value contains:
        - customer_id, customer_name
        - project_ids (deduped, sorted)
        - rows (all ReportRow items for that customer)
        - recipients (initially empty; filled by attach_recipient_emails_from_project_followers)
    """
    groups: Dict[str, CustomerPacket] = {}
    projects_per_customer: Dict[str, Set[str]] = defaultdict(set)

    for r in rows:
        if r.customer_id not in groups:
            groups[r.customer_id] = CustomerPacket(
                customer_id=r.customer_id,
                customer_name=r.customer_name,
                project_ids=[],
                recipients=[],
                rows=[]
            )
        groups[r.customer_id]["rows"].append(r)
        if r.project_id:
            projects_per_customer[r.customer_id].add(str(r.project_id))

    # finalize project_ids (deduped + sorted)
    for cid, packet in groups.items():
        packet["project_ids"] = sorted(projects_per_customer[cid])

    return groups


def attach_recipient_emails_from_project_followers(
    groups: Dict[str, CustomerPacket],
    odoo_client: object,
    *,
    fallback_if_empty: Optional[str] = None,
) -> None:
    """
    For each customer, gather recipient emails from all involved projects' followers.

    Behavior:
    - If EMAIL_FORWARD_ALL_TO is set, every customer gets ONLY that address (safe testing).
    - Otherwise, union all follower emails across the customer's projects (deduped + sorted).
    - If a customer has no followers and `fallback_if_empty` is provided, use that address.

    Args:
        groups: Output of group_rows_by_customer_id
        odoo_client: Must expose either `fetch_project_follower_emails(project_id)` or
                    (for back-compat) `get_project_followers(project_id)`
        fallback_if_empty: Optional single email used when a customer has no followers
    """
    forward_all = os.getenv("EMAIL_FORWARD_ALL_TO", "").strip()

    # Choose the best available method on the client (new name first, then legacy)
    fetch_followers = getattr(odoo_client, "fetch_project_follower_emails", None)
    if not callable(fetch_followers):
        fetch_followers = getattr(odoo_client, "get_project_followers", None)

    for cid, packet in groups.items():
        if forward_all:
            packet["recipients"] = [forward_all]
            continue

        emails: Set[str] = set()
        if callable(fetch_followers):
            for pid in packet["project_ids"]:
                try:
                    follower_emails = cast(List[str], fetch_followers(pid) or [])
                    for e in follower_emails:
                        e = (e or "").strip()
                        if "@" in e:
                            emails.add(e)
                except Exception as exc:
                    # Keep going; log to stdout for now (replace with logging later)
                    print(f"[WARN] followers fetch failed for project {pid}: {exc}")

        if not emails and fallback_if_empty:
            packet["recipients"] = [fallback_if_empty]
        else:
            packet["recipients"] = sorted(emails)

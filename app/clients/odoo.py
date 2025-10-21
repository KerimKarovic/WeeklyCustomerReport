# app/clients/odoo.py
from __future__ import annotations
import os, json, pathlib
from datetime import date
from typing import List, Dict, Any, Optional, Tuple, Iterable
from urllib.parse import urlparse

from app.services.report_row import (
    ReportRow,
    parse_date_from_iso_string,
    normalize_work_classification,
    normalize_task_status_from_odoo,
)


class OdooClient:
    """
    Odoo data source with a simple 'stub → real' switch.

    - Stub mode (default): reads JSON from /samples for fast, safe development.
    - Real mode: XML-RPC + email/password auth.
    """

    def __init__(self, root_dir: Optional[str] = None) -> None:
        # Base connection info
        self.base_url = (os.getenv("ODOO_BASE_URL", "") or "").rstrip("/")
        self.db = os.getenv("ODOO_DB", "")
        self.login = os.getenv("ODOO_USERNAME", "")
        self.password = os.getenv("ODOO_PASSWORD", "")

        # Optional timeout
        self.timeout = int(os.getenv("ODOO_TIMEOUT_SECONDS", "25"))

        # Project filter
        self.env_project_ids = {
            s.strip() for s in os.getenv("REPORT_PROJECT_IDS", "").split(",") if s.strip()
        }

        # Paths
        self.root = pathlib.Path(root_dir or pathlib.Path(__file__).resolve().parents[2])
        self.samples_dir = self.root / "samples"

        # Auto mode: real if all creds present, else stub
        self.use_stub = not all([self.base_url, self.db, self.login, self.password])

        mode = "STUB (samples)" if self.use_stub else "REAL (XML-RPC, password)"
        print(f"[OdooClient] mode={mode} url={self.base_url or '-'} db={self.db or '-'}")


    def _make_transport_and_module(self, is_https: bool):
        """Lazy-import xmlrpc + http and return a configured transport and xmlrpc module.
        This avoids importing stdlib 'email' via http.client when running in stub mode.
        """
        import xmlrpc.client as xc
        import http.client as hc

        class TimeoutTransport(xc.Transport):
            def __init__(self, timeout: int = 25, use_datetime: bool = False):
                super().__init__(use_datetime=use_datetime)
                self._timeout = timeout
            def make_connection(self, host):
                if isinstance(host, tuple):
                    host = host[0]
                return hc.HTTPConnection(host, timeout=self._timeout)

        class TimeoutHTTPSTransport(xc.SafeTransport):
            def __init__(self, timeout: int = 25, use_datetime: bool = False):
                super().__init__(use_datetime=use_datetime)
                self._timeout = timeout
            def make_connection(self, host):
                if isinstance(host, tuple):
                    host = host[0]
                return hc.HTTPSConnection(host, timeout=self._timeout)

        transport = TimeoutHTTPSTransport(timeout=self.timeout) if is_https else TimeoutTransport(timeout=self.timeout)
        return transport, xc

    def fetch_timesheet_rows(
        self,
        start: date,
        end: date,
        project_ids: Optional[List[str]] = None,
    ) -> List[ReportRow]:
        """Return ReportRow list for [start..end] inclusive."""
        project_filter = set(project_ids or []) or self.env_project_ids

        if self.use_stub:
            return self._fake_fetch_timesheet_rows(start, end, project_filter)


        uid, models = self._rpc_authenticate()

        # Build domain for timesheet query
        domain = [
            ["date", ">=", start.isoformat()],
            ["date", "<=", end.isoformat()]
        ]

        # Fields available in your Odoo instance + sales order line for classification
        fields = [
            "id", "date", "unit_amount", "name", "employee_id",
            "task_id", "project_id", "partner_id", "so_line"
        ]

        # Fetch timesheets
        timesheets = models.execute_kw(
            self.db, uid, self.password,
            "account.analytic.line", "search_read",
            [domain], {"fields": fields}
        )

        # Get task status information for all tasks
        task_ids = [ts["task_id"][0] for ts in timesheets if ts.get("task_id")]
        task_status_map = {}
        if task_ids:
            tasks = models.execute_kw(
                self.db, uid, self.password,
                "project.task", "read",
                [list(set(task_ids))], {"fields": ["id", "stage_id", "state"]}
            )
            for task in tasks:
                stage_name = task.get("stage_id", [None, ""])[1] if task.get("stage_id") else ""
                task_status_map[task["id"]] = stage_name

        # Convert to ReportRow objects with proper enrichment
        rows = []
        for ts in timesheets:
            rr = self._enrich_timesheet_row(ts, task_status_map)

            # Apply project filter
            if project_filter and str(rr.project_id) not in project_filter:
                continue

            rows.append(rr)

        return rows

    def get_project_followers(self, project_id: str | int) -> List[str]:
        """Return email addresses of project followers."""
        if self.use_stub:
            projects = self._load_json(self.samples_dir / "odoo_projects.json")
            for p in projects:
                if str(p.get("project_id")) == str(project_id):
                    emails = p.get("followers", [])
                    return self._clean_emails(emails)
            return []

        uid, models = self._rpc_authenticate()

        try:
            # Get project with follower IDs
            project = models.execute_kw(
                self.db, uid, self.password,
                "project.project", "read",
                [int(project_id)], {"fields": ["message_follower_ids"]}
            )

            if not project:
                return []

            follower_ids = project[0].get("message_follower_ids", [])
            if not follower_ids:
                return []

            # Get followers to find partner IDs
            followers = models.execute_kw(
                self.db, uid, self.password,
                "mail.followers", "read",
                [follower_ids], {"fields": ["partner_id"]}
            )

            partner_ids = [f["partner_id"][0] for f in followers if f.get("partner_id")]
            if not partner_ids:
                return []

            # Get partner emails
            partners = models.execute_kw(
                self.db, uid, self.password,
                "res.partner", "read",
                [partner_ids], {"fields": ["email"]}
            )

            emails = [p.get("email", "").strip() for p in partners]
            return self._clean_emails(emails)

        except Exception as exc:
            print(f"[WARN] Failed to fetch followers for project {project_id}: {exc}")
            return []

    def _rpc_authenticate(self) -> Tuple[int, Any]:
        if not (self.base_url and self.db and self.login and self.password):
            raise RuntimeError("Missing ODOO credentials")

        parsed_url = urlparse(self.base_url)
        is_https = parsed_url.scheme.lower() == 'https'

        transport, xc = self._make_transport_and_module(is_https)

        common = xc.ServerProxy(f"{self.base_url}/xmlrpc/2/common", transport=transport, allow_none=True)
        uid = common.authenticate(self.db, self.login, self.password, {})
        if not uid or not isinstance(uid, int):
            raise RuntimeError("Odoo authentication failed")

        models = xc.ServerProxy(f"{self.base_url}/xmlrpc/2/object", transport=transport, allow_none=True)
        return uid, models

    def _fake_fetch_timesheet_rows(self, start: date, end: date, project_filter: set[str]) -> List[ReportRow]:
        raw = self._load_json(self.samples_dir / "odoo_timesheets.json")
        rows: List[ReportRow] = []
        for e in raw:
            d = parse_date_from_iso_string(e["date"])
            if not (start <= d <= end):
                continue
            rr = ReportRow(
                worklog_id=int(e["worklog_id"]),
                date=d,
                task_id=int(e["task_id"]),
                task_name=str(e.get("task_name", "")),
                task_url=str(e.get("task_url", "")),
                user=str(e.get("user", "")),
                hours=float(e.get("hours", 0.0)),
                classification=normalize_work_classification(e.get("classification")),
                task_status=normalize_task_status_from_odoo(e.get("task_status")),
                customer_id=str(e.get("customer_id", "")),
                customer_name=str(e.get("customer_name", "")),
                project_id=str(e.get("project_id", "")),
                project_name=str(e.get("project_name", "")),
            )
            if project_filter and str(rr.project_id) not in project_filter:
                continue
            rows.append(rr)
        return rows

    @staticmethod
    def _clean_emails(emails: Iterable[str]) -> List[str]:
        return sorted({e.strip() for e in emails if e and "@" in e})

    @staticmethod
    def _load_json(path: pathlib.Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Missing JSON sample file: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _enrich_timesheet_row(self, ts: Dict[str, Any], task_status_map: Optional[Dict[int, str]] = None) -> ReportRow:
        """Convert raw Odoo timesheet record to enriched ReportRow."""
        # Extract M2O fields safely
        task_info = ts.get("task_id") or []
        project_info = ts.get("project_id") or []
        employee_info = ts.get("employee_id") or []
        partner_info = ts.get("partner_id") or []
        so_line_info = ts.get("so_line") or []

        # Extract IDs and names with fallbacks
        task_id = int(task_info[0]) if task_info and len(task_info) > 0 else 0
        task_name = str(task_info[1]) if task_info and len(task_info) > 1 else ""

        project_id = str(project_info[0]) if project_info and len(project_info) > 0 else ""
        project_name = str(project_info[1]) if project_info and len(project_info) > 1 else ""

        user = str(employee_info[1]) if employee_info and len(employee_info) > 1 else ""

        customer_id = str(partner_info[0]) if partner_info and len(partner_info) > 0 else ""
        customer_name = str(partner_info[1]) if partner_info and len(partner_info) > 1 else ""

        # Extract classification from sales order line description
        so_line_description = str(so_line_info[1]) if so_line_info and len(so_line_info) > 1 else ""
        classification = self._extract_classification_from_so_line(so_line_description)

        # Build task deep link URL
        task_url = f"{self.base_url}/web#id={task_id}&model=project.task" if task_id else ""

        # Get task status from the map we built
        task_stage_name = task_status_map.get(task_id, "") if task_status_map else ""
        task_status = normalize_task_status_from_odoo(task_stage_name)

        return ReportRow(
            worklog_id=int(ts["id"]),
            date=parse_date_from_iso_string(ts["date"]),
            task_id=task_id,
            task_name=task_name,
            task_url=task_url,
            user=user,
            hours=float(ts.get("unit_amount", 0.0)),
            classification=normalize_work_classification(classification),
            task_status=task_status,
            customer_id=customer_id,
            customer_name=customer_name,
            project_id=project_id,
            project_name=project_name,
            description=str(ts.get("name", ""))  # Capture the worklog description
        )

    def _extract_classification_from_so_line(self, so_line_description: str) -> str:
        """
        Extract work classification from sales order line description.

        Examples from your Odoo:
        - "SO2174 - Interne Aufwände (99999)" → "Service" (internal development)
        - "SO1988 - Softwareentwicklung (projektbezogen nach Aufwand)" → "Service"
        - "SO2197 - IT Beratung u. Service (Projektbez. nach Aufwand)" → "Support"
        - "SO1150 - Kulanz (projektbezogen) (10107)" → "Kulanz"
        """
        description = so_line_description.lower()

        # Kulanz work = Kulanz (highest priority)
        if any(keyword in description for keyword in [
            "kulanz", "goodwill"
        ]):
            return "Kulanz"

        # Development work = Service
        if any(keyword in description for keyword in [
            "softwareentwicklung", "entwicklung", "interne aufwände",
            "investition", "implementation", "umsetzung"
        ]):
            return "Service"

        # Support/consulting work = Support
        if any(keyword in description for keyword in [
            "it beratung", "service", "support", "wartung", "beratung",
            "fehlerbehebung", "hotline", "emailsupport"
        ]):
            return "Support"

        # Default to Support for unclear cases
        return "Support"

    def fetch_customer_address(self, partner_id: str | int) -> dict:
        """Fetch customer address, following parent company if needed."""
        if self.use_stub:
            # Return sample address for stub mode
            return {
                "street": "Musterstraße 123",
                "zip": "12345", 
                "city": "Musterstadt",
                "country": "Deutschland"
            }
        
        uid, models = self._rpc_authenticate()
        
        try:
            # Fetch partner with address and company info
            partner = models.execute_kw(self.db, uid, self.password, 'res.partner', 'read', 
                [int(partner_id)], 
                {'fields': ['name', 'is_company', 'parent_id', 'street', 'zip', 'city', 'country_id']}
            )[0]
            
            # If this is an individual, get parent company address
            if not partner.get('is_company', False) and partner.get('parent_id'):
                parent_id = partner['parent_id'][0]
                parent = models.execute_kw(self.db, uid, self.password, 'res.partner', 'read',
                    [parent_id],
                    {'fields': ['street', 'zip', 'city', 'country_id']}
                )[0]
                partner.update(parent)  # Use parent's address
            
            # Extract address components
            country_name = partner.get('country_id', [False, 'Deutschland'])[1] if partner.get('country_id') else 'Deutschland'
            
            return {
                "street": partner.get('street', '') or '',
                "zip": partner.get('zip', '') or '',
                "city": partner.get('city', '') or '',
                "country": country_name
            }
            
        except Exception as exc:
            print(f"[WARN] Failed to fetch address for partner {partner_id}: {exc}")
            return {"street": "", "zip": "", "city": "", "country": "Deutschland"}


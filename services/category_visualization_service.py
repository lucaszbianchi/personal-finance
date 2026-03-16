"""Service for category visualization data (expense history & distribution)."""

from collections import defaultdict
from datetime import date

from repositories.category_visualization_repository import CategoryVisualizationRepository


def _months_back(n: int) -> str:
    """Return YYYY-MM-01 for n full months before the current month."""
    today = date.today()
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}-01"


class CategoryVisualizationService:
    def __init__(self):
        self.repo = CategoryVisualizationRepository()

    def get_expense_history(self, months: int = 6) -> dict:
        """Monthly expense totals per category for the last N months."""
        start_date = _months_back(months)
        rows = self.repo.get_expenses_by_month_and_category(start_date)

        # Aggregate (month, category_id) across bank + credit rows
        monthly: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        cat_names: dict[str, str] = {}
        for row in rows:
            monthly[row["month"]][row["category_id"]] += row["total"]
            cat_names[row["category_id"]] = row["category_name"]

        all_months = sorted(monthly.keys())

        series_map: dict[str, dict] = {}
        for month in all_months:
            for cat_id, total in monthly[month].items():
                if cat_id not in series_map:
                    series_map[cat_id] = {
                        "id": cat_id,
                        "name": cat_names.get(cat_id, cat_id),
                        "_by_month": {},
                        "total": 0.0,
                    }
                series_map[cat_id]["_by_month"][month] = round(total, 2)
                series_map[cat_id]["total"] += total

        series = sorted(series_map.values(), key=lambda x: x["total"], reverse=True)
        for s in series:
            s["data"] = [round(s["_by_month"].get(m, 0), 2) for m in all_months]
            s["total"] = round(s["total"], 2)
            del s["_by_month"]

        return {"months": all_months, "series": series}

    def get_expense_distribution(self, month: str) -> dict:
        """Hierarchical expense breakdown for Sankey: total → groups → categories."""
        rows = self.repo.get_expenses_by_category(month)

        # Aggregate same category_id across bank + credit
        cat_data: dict[str, dict] = {}
        for row in rows:
            cid = row["category_id"]
            if cid not in cat_data:
                cat_data[cid] = {
                    "category_id": cid,
                    "category_name": row["category_name"],
                    "parent_id": row["parent_id"],
                    "parent_name": row["parent_name"],
                    "total": 0.0,
                }
            cat_data[cid]["total"] += row["total"]

        groups: dict[str, dict] = {}
        grand_total = 0.0

        for data in cat_data.values():
            cat_id = data["category_id"]
            cat_name = data["category_name"]
            parent_id = data["parent_id"]
            parent_name = data["parent_name"]
            amount = data["total"]
            grand_total += amount

            is_own_parent = parent_id is None or parent_id == cat_id
            group_id = cat_id if is_own_parent else parent_id
            group_name = cat_name if is_own_parent else parent_name

            if group_id not in groups:
                groups[group_id] = {
                    "id": group_id,
                    "name": group_name,
                    "total": 0.0,
                    "categories": [],
                }
            groups[group_id]["total"] += amount

            if not is_own_parent:
                groups[group_id]["categories"].append({
                    "id": cat_id,
                    "name": cat_name,
                    "total": round(amount, 2),
                })

        result_groups = sorted(groups.values(), key=lambda x: x["total"], reverse=True)
        for g in result_groups:
            g["total"] = round(g["total"], 2)
            g["categories"].sort(key=lambda x: x["total"], reverse=True)

        return {
            "month": month,
            "total": round(grand_total, 2),
            "groups": result_groups,
        }

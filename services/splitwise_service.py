from typing import List, Optional, Dict, Any
from datetime import datetime
from repositories.person_repository import PersonRepository
from repositories.splitwise_repository import SplitwiseRepository
from repositories.transaction_repository import TransactionRepository
from models.splitwise import Splitwise
from utils.date_helper import DateHelper


class SplitwiseService:
    def __init__(self, db_path: str = "finance.db"):
        self.splitwise_repository = SplitwiseRepository(db_path)
        self.person_repository = PersonRepository(db_path)
        self.transaction_repository = TransactionRepository(db_path)
        self.date_helper = DateHelper()

    def get_all_splitwise(self) -> List[Splitwise]:
        """Retorna todas as transações do Splitwise."""
        return self.splitwise_repository.get_all_splitwise()

    def get_all_splitwise_with_match_info(self) -> List[dict]:
        """Retorna todas as transações do Splitwise com informações de match."""
        query = """
            SELECT
                s.id,
                s.amount,
                s.date,
                s.description,
                s.category_id,
                s.transaction_id,
                s.match_type,
                c.name as category_name
            FROM splitwise s
            LEFT JOIN categories c ON s.category_id = c.id
            ORDER BY s.date DESC
        """
        cursor = self.splitwise_repository.execute_query(query)
        results = []

        for row in cursor.fetchall():
            # Determine match status for UI
            match_status = None
            linked_transaction = None

            if row["transaction_id"]:
                match_status = (
                    row["match_type"] or "manual"
                )  # Default to manual if no match_type
                linked_transaction = row["transaction_id"]

            results.append(
                {
                    "id": row["id"],
                    "amount": row["amount"],
                    "date": row["date"],
                    "description": row["description"],
                    "category_id": row["category_id"],
                    "category": row["category_name"] or "",
                    "transaction_id": row["transaction_id"],
                    "match_status": match_status,
                    "linked_transaction": linked_transaction,
                }
            )

        return results

    def get_splitwise_by_id(self, splitwise_id: str) -> Optional[Splitwise]:
        """Retorna uma transação específica do Splitwise pelo ID."""
        return self.splitwise_repository.get_splitwise_by_id(splitwise_id)

    def get_splitwise_by_transaction(self, transaction_id: str) -> Optional[Splitwise]:
        """Retorna a transação do Splitwise vinculada a uma transação específica."""
        return self.splitwise_repository.get_splitwise_by_transaction_id(transaction_id)

    def link_transaction_to_splitwise(self, splitwise_id: str, transaction_id: str):
        """Vincula uma transação ao splitwise"""
        splitwise = self.splitwise_repository.get_splitwise_by_id(splitwise_id)
        if not splitwise:
            raise ValueError("Splitwise não encontrado")
        return self.splitwise_repository.set_transaction_to_splitwise(
            splitwise_id, transaction_id
        )

    def get_unsettled_splitwise(self) -> List[Splitwise]:
        """Retorna splitwise sem transação vinculada."""
        return self.splitwise_repository.get_unsettled_splitwise()

    def get_splitwise_summary(self) -> dict:
        """Retorna um resumo das transações do Splitwise."""
        splitwise_entries = self.splitwise_repository.get_all_splitwise()

        summary = {
            "total_entries": len(splitwise_entries),
            "total_amount": sum(entry.amount for entry in splitwise_entries),
            "settled": {
                "count": len([e for e in splitwise_entries if e.transaction_id]),
                "amount": sum(e.amount for e in splitwise_entries if e.transaction_id),
            },
            "unsettled": {
                "count": len([e for e in splitwise_entries if not e.transaction_id]),
                "amount": sum(
                    e.amount for e in splitwise_entries if not e.transaction_id
                ),
            },
        }

        return summary

    def update_splitwise(
        self, splitwise_id: str, category_id: str, transaction_id: str
    ):
        """Atualiza um registro do Splitwise."""
        splitwise = self.splitwise_repository.get_splitwise_by_id(splitwise_id)
        if not splitwise:
            raise ValueError("Splitwise não encontrado")
        return self.splitwise_repository.update_splitwise(
            splitwise_id, category_id, transaction_id
        )

    def category_in_use(self, category_id: str) -> bool:
        """Verifica se uma categoria está em uso no Splitwise."""
        return self.splitwise_repository.category_in_use(category_id)

    # ========== Matching Methods (moved from SplitwiseMatchingService) ==========

    def auto_match_splitwise_transactions(self) -> Dict[str, Any]:
        """
        Main orchestrator for auto-matching Splitwise transactions.

        Returns:
            Dict containing match results and statistics
        """
        results = {
            "total_processed": 0,
            "matches_found": 0,
            "matches_applied": 0,
            "errors": [],
        }

        try:
            # Get all unmatched Splitwise transactions
            unmatched_splitwise = self.splitwise_repository.get_unsettled_splitwise()
            results["total_processed"] = len(unmatched_splitwise)

            print(
                f"Processing {len(unmatched_splitwise)} unmatched Splitwise transactions..."
            )

            for splitwise_entry in unmatched_splitwise:
                try:
                    match = self.find_matching_transaction(splitwise_entry)
                    if match:
                        results["matches_found"] += 1
                        if self.apply_match(splitwise_entry, match):
                            results["matches_applied"] += 1
                            print(
                                f"Auto-matched: {splitwise_entry.description} -> {match.description}"
                            )

                except Exception as e:
                    error_msg = (
                        f"Error processing {splitwise_entry.splitwise_id}: {str(e)}"
                    )
                    results["errors"].append(error_msg)
                    print(f"Error: {error_msg}")

        except Exception as e:
            error_msg = f"Critical error in auto-matching: {str(e)}"
            results["errors"].append(error_msg)
            print(f"Critical error: {error_msg}")

        print(
            f"Auto-matching complete: {results['matches_applied']}/{results['total_processed']} matched"
        )
        return results

    def find_matching_transaction(self, splitwise_entry: Splitwise) -> Optional[Any]:
        """
        Find single best matching transaction for a Splitwise entry.

        Args:
            splitwise_entry: Splitwise transaction to match

        Returns:
            Matching transaction if exactly one match found, None otherwise
        """
        try:
            # Parse the Splitwise date
            splitwise_date = self._parse_date(splitwise_entry.date)
            if not splitwise_date:
                return None

            # Get all bank and credit transactions for the same date
            same_date_transactions = []

            # Get bank transactions for the date
            bank_transactions = self.splitwise_repository.get_bank_transactions_by_date(
                splitwise_date.strftime("%Y-%m-%d")
            )
            same_date_transactions.extend(bank_transactions)

            # Get credit transactions for the date
            credit_transactions = (
                self.splitwise_repository.get_credit_transactions_by_date(
                    splitwise_date.strftime("%Y-%m-%d")
                )
            )
            same_date_transactions.extend(credit_transactions)

            # Filter by amount (±2% tolerance)
            # Splitwise values are typically half of the transaction (what user lent to person)
            amount_matches = []
            for transaction in same_date_transactions:
                tx_amount = abs(transaction.amount)
                splitwise_amount = abs(splitwise_entry.amount)

                # Check if Splitwise amount matches ~50% of transaction (±2% tolerance on each)
                half_tx_amount = tx_amount / 2
                if self._amounts_match(splitwise_amount, half_tx_amount):
                    # Check if transaction is already linked to another Splitwise entry
                    if not self._is_transaction_already_linked(
                        transaction.transaction_id
                    ):
                        amount_matches.append(transaction)

            # Return match only if exactly one transaction matches both criteria
            if len(amount_matches) == 1:
                return amount_matches[0]

            return None

        except Exception as e:
            print(f"Error finding match for {splitwise_entry.splitwise_id}: {e}")
            return None

    def apply_match(self, splitwise_entry: Splitwise, transaction: Any) -> bool:
        """
        Apply an automatic match between Splitwise entry and transaction.

        Args:
            splitwise_entry: Splitwise transaction
            transaction: Bank or credit transaction to link

        Returns:
            True if match was applied successfully, False otherwise
        """
        try:
            # Set the transaction link
            success = self.splitwise_repository.set_transaction_to_splitwise(
                splitwise_entry.splitwise_id, transaction
            )

            if success:
                # Update match_type to 'auto'
                self.splitwise_repository.update_match_type(
                    splitwise_entry.splitwise_id, "auto"
                )
                return True

            return False

        except Exception as e:
            print(f"Error applying match for {splitwise_entry.splitwise_id}: {e}")
            return False

    def get_matching_statistics(self) -> Dict[str, Any]:
        """Get statistics about current matching state."""
        try:
            stats = {}

            # Count total Splitwise entries
            all_splitwise = self.splitwise_repository.get_all_splitwise()
            stats["total_splitwise"] = len(all_splitwise)

            # Count by match type
            query = """
                SELECT match_type, COUNT(*) as count
                FROM splitwise
                GROUP BY match_type
            """
            cursor = self.splitwise_repository.execute_query(query)
            match_counts = {
                row["match_type"] or "unmatched": row["count"]
                for row in cursor.fetchall()
            }

            stats["auto_matched"] = match_counts.get("auto", 0)
            stats["manual_matched"] = match_counts.get("manual", 0)
            stats["unmatched"] = match_counts.get("unmatched", 0)

            # Calculate percentages
            if stats["total_splitwise"] > 0:
                stats["auto_match_rate"] = (
                    stats["auto_matched"] / stats["total_splitwise"]
                ) * 100
                stats["total_match_rate"] = (
                    (stats["auto_matched"] + stats["manual_matched"])
                    / stats["total_splitwise"]
                ) * 100
            else:
                stats["auto_match_rate"] = 0
                stats["total_match_rate"] = 0

            return stats

        except Exception as e:
            print(f"Error getting matching statistics: {e}")
            return {}

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        try:
            # Handle DateHelper format: "2025-10-09\n09:17:57"
            if "\n" in date_str:
                date_part = date_str.split("\n")[0]
                return datetime.strptime(date_part, "%Y-%m-%d")
            # Handle ISO format: 2025-10-07T13:08:53.002Z
            elif "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            # Handle simple date format: 2025-10-07
            else:
                return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    def _amounts_match(
        self, amount1: float, amount2: float, tolerance: float = 0
    ) -> bool:
        """
        Check if two amounts match within tolerance.

        Args:
            amount1: First amount (Splitwise)
            amount2: Second amount (transaction)
            tolerance: Tolerance percentage (0.02 = 2%)
        """
        if amount1 == 0 or amount2 == 0:
            return amount1 == amount2

        # Calculate the percentage difference
        diff = abs(amount1 - amount2) / max(abs(amount1), abs(amount2))
        return diff <= tolerance

    def _is_transaction_already_linked(self, transaction_id: str) -> bool:
        """Check if a transaction is already linked to another Splitwise entry."""
        existing_splitwise = self.splitwise_repository.get_splitwise_by_transaction_id(
            transaction_id
        )
        return existing_splitwise is not None

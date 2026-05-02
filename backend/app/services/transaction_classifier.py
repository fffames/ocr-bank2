"""Transaction classifier service using string matching for reliable classification."""
from typing import Dict, Optional


class TransactionClassifier:
    """Classify receipts as sending (paying) or receiving (income)."""

    def __init__(self):
        """Initialize the transaction classifier."""
        pass

    def classify(
        self,
        sender: Optional[str],
        receiver: Optional[str],
        user_name: str,
        name_variations: list = None
    ) -> Dict[str, any]:
        """
        Determine if user is sending or receiving money using TEXT data only.

        Args:
            sender: Sender name from OCR (text from database)
            receiver: Receiver name from OCR (text from database)
            user_name: User's actual name
            name_variations: List of name variations for fuzzy matching

        Returns:
            {
                "transaction_type": "sending" | "receiving" | "unknown",
                "confidence": "high" | "medium" | "low",
                "reason": "Explanation of why classified this way"
            }
        """

        if not user_name or not user_name.strip():
            return {
                "transaction_type": "unknown",
                "confidence": "low",
                "reason": "No user name provided"
            }

        # Use string matching as primary method (fast, reliable, handles OCR errors well)
        return self._fallback_classify(sender, receiver, user_name, name_variations)

    def _fallback_classify(
        self,
        sender: Optional[str],
        receiver: Optional[str],
        user_name: str,
        name_variations: Optional[list]
    ) -> Dict[str, any]:
        """Simple string matching fallback (no LLM)."""

        # Build list of names to match
        names_to_match = [user_name]
        if name_variations:
            names_to_match.extend(name_variations)

        # Check sender
        if sender:
            for name in names_to_match:
                if name in sender:
                    return {
                        "transaction_type": "sending",
                        "confidence": "medium",
                        "reason": f"User's name '{name}' found in sender field"
                    }

        # Check receiver
        if receiver:
            for name in names_to_match:
                if name in receiver:
                    return {
                        "transaction_type": "receiving",
                        "confidence": "medium",
                        "reason": f"User's name '{name}' found in receiver field"
                    }

        # Unknown
        return {
            "transaction_type": "unknown",
            "confidence": "low",
            "reason": "Could not match user's name in sender or receiver"
        }

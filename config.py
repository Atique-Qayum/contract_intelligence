"""Shared settings. FX rates are ILLUSTRATIVE ASSUMPTIONS for the demo, not market rates."""
FX_TO_EUR = {"EUR": 1.0, "USD": 0.92, "SGD": 0.69}
ALLOWED_CURRENCIES = set(FX_TO_EUR)
HIGH_VALUE_EUR = 300_000  # contracts at/above this always go to human review
REQUIRED_FIELDS = ["contract_id", "client_name_raw", "programme", "contract_value",
                   "payment_terms", "cancellation_terms"]

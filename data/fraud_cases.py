"""
Mock fraud-case database for ResolveAI (Banking & Insurance track —
Real-Time Fraud Intervention). Simulates the institutional systems a
real bank would expose (fraud detection, card management, transaction
processing) — no real customer or financial data.

SECURITY NOTE: `verification_code` represents an OTP-style code that,
in a real deployment, would be freshly generated per contact attempt
by the bank's own fraud system and sent to the customer's registered
channel (SMS/app push) — never generated or known by the voice agent
in advance. This sandbox uses a fixed code per record so the demo and
test suite are reproducible. No tool in tools.py exposes this value to
the agent; verification is a server-side string comparison, never an
agent-asserted boolean. See tools.py:verify_customer.

CARDS holds current card status, separately from cases, so the
idempotency test (freezing twice) has somewhere real to check state
against — this is not just a flag on the case.
"""

CARDS = {
    "CARD-8821": {"card_id": "CARD-8821", "last4": "8821", "customer_id": "CUS-DEMO-1001", "status": "ACTIVE"},
    "CARD-4192": {"card_id": "CARD-4192", "last4": "4192", "customer_id": "CUS-DEMO-1002", "status": "ACTIVE"},
    "CARD-7734": {"card_id": "CARD-7734", "last4": "7734", "customer_id": "CUS-DEMO-1003", "status": "ACTIVE"},
    "CARD-5510": {"card_id": "CARD-5510", "last4": "5510", "customer_id": "CUS-DEMO-1004", "status": "ACTIVE"},
    "CARD-9903": {"card_id": "CARD-9903", "last4": "9903", "customer_id": "CUS-DEMO-1005", "status": "ACTIVE"},
}

FRAUD_CASES = {
    "CASE-2001": {
        "case_id": "CASE-2001",
        "customer_id": "CUS-DEMO-1001",
        "card_id": "CARD-8821",
        "verification_code": "4471",
        "fraud_type": "CARD_NOT_PRESENT_ONLINE",
        "fraud_description": "Unusual card-not-present purchase at an online merchant not matching your usual spending pattern",
        "transaction": {
            "amount": 4850,
            "currency": "AED",
            "merchant": "DEMO MERCHANT ONLINE",
            "status": "PENDING",  # PENDING -> BLOCKED once frozen
        },
        "requires_dual_authorization": False,
        "supported": True,
        "preferred_language": "en",
    },
    "CASE-2002": {
        "case_id": "CASE-2002",
        "customer_id": "CUS-DEMO-1002",
        "card_id": "CARD-4192",
        "verification_code": "8823",
        "fraud_type": "GEO_VELOCITY_MISMATCH",
        "fraud_description": "Two card transactions in different countries within a window too short for physical travel",
        "transaction": {
            "amount": 612,
            "currency": "AED",
            "merchant": "DEMO MERCHANT TRAVEL",
            "status": "PENDING",
        },
        "requires_dual_authorization": False,
        "supported": True,
        "preferred_language": "ar",  # used in the Arabic-customer demo
    },
    "CASE-2003": {
        "case_id": "CASE-2003",
        "customer_id": "CUS-DEMO-1003",
        "card_id": "CARD-7734",
        "verification_code": "1190",
        "fraud_type": "HIGH_VALUE_ANOMALY",
        "fraud_description": "A high-value transaction well above your typical spend, flagged for additional review",
        "transaction": {
            "amount": 38500,
            "currency": "AED",
            "merchant": "DEMO MERCHANT ELECTRONICS",
            "status": "PENDING",
        },
        "requires_dual_authorization": True,  # above threshold — agent cannot freeze alone
        "supported": True,
        "preferred_language": "en",
    },
    "CASE-2004": {
        "case_id": "CASE-2004",
        "customer_id": "CUS-DEMO-1004",
        "card_id": "CARD-5510",
        "verification_code": "5502",
        "fraud_type": "CARD_NOT_PRESENT_ONLINE",
        "fraud_description": "A card-not-present purchase flagged as unusual for your account",
        "transaction": {
            "amount": 950,
            "currency": "AED",
            "merchant": "DEMO MERCHANT RETAIL",
            "status": "PENDING",
        },
        "requires_dual_authorization": False,
        "supported": True,  # scripted in the demo to be DISPUTED by the customer (it's actually theirs)
        "preferred_language": "en",
    },
    "CASE-2005": {
        "case_id": "CASE-2005",
        "customer_id": "CUS-DEMO-1005",
        "card_id": "CARD-9903",
        "verification_code": "6634",
        "fraud_type": "SUSPECTED_ACCOUNT_TAKEOVER",
        "fraud_description": "Pattern consistent with account takeover (credential/device change shortly before transaction)",
        "transaction": {
            "amount": 12300,
            "currency": "AED",
            "merchant": "DEMO MERCHANT DIGITAL GOODS",
            "status": "PENDING",
        },
        "requires_dual_authorization": False,
        "supported": False,  # no approved automated policy for this fraud type — must escalate
        "preferred_language": "en",
    },
}

# ---------------------------------------------------------------------------
# Reset support — both tools.py's confirm_fraud_and_freeze and this being
# in-memory mock data means CARDS/FRAUD_CASES genuinely mutate (card status
# flips to FROZEN, transaction status flips to BLOCKED). Both the test
# suite and server.py's /api/demo/reset need to restore pristine state
# without re-importing the module (which wouldn't help — Python caches
# imports). This captures a snapshot once, at first use, and restores
# from it on request.
# ---------------------------------------------------------------------------
import copy as _copy

_INITIAL_CASES_SNAPSHOT = _copy.deepcopy(FRAUD_CASES)
_INITIAL_CARDS_SNAPSHOT = _copy.deepcopy(CARDS)


def reset_mock_data() -> None:
    """Restores FRAUD_CASES and CARDS to their initial state in place —
    mutates existing dict entries rather than rebinding the module-level
    names, so other modules that did `from data.fraud_cases import
    FRAUD_CASES, CARDS` continue to see the same (now-reset) objects."""
    for case_id, original in _INITIAL_CASES_SNAPSHOT.items():
        FRAUD_CASES[case_id] = _copy.deepcopy(original)
    for card_id, original in _INITIAL_CARDS_SNAPSHOT.items():
        CARDS[card_id] = _copy.deepcopy(original)

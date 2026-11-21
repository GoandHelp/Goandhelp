"""Read-only checkout regressions: AST inspection and real Stripe SDK encoding."""

import ast
from pathlib import Path
import unittest

from stripe._encode import _api_encode

from app.membership import PLAN_INTERVAL, PLAN_PRICE_CENTS, PLAN_PRODUCT_NAME


class StripeCheckoutManagedPaymentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).with_name("membership.py").read_text()
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "create_checkout_session"
        )
        calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "asyncio.to_thread"
            and node.args
            and ast.unparse(node.args[0]) == "stripe.checkout.Session.create"
        ]
        if len(calls) != 1:
            raise AssertionError(
                "Expected exactly one subscription Checkout creation call"
            )
        cls.call = calls[0]
        cls.kwargs = {
            keyword.arg: keyword.value for keyword in cls.call.keywords
        }

    def test_explicit_standard_subscription_checkout(self):
        self.assertEqual(ast.literal_eval(self.kwargs["mode"]), "subscription")
        managed_payments = ast.literal_eval(self.kwargs["managed_payments"])
        self.assertEqual(set(managed_payments), {"enabled"})
        self.assertIs(managed_payments["enabled"], False)
        self.assertEqual(len(self.call.args), 1)
        self.assertEqual(len(self.call.keywords), len(self.kwargs))

    def test_existing_checkout_arguments_unchanged(self):
        expected = {
            "api_key": "key",
            "mode": "'subscription'",
            "customer": "customer_id",
            "client_reference_id": "str(subscriber_id)",
            "success_url": "checkout_success_url(base_url)",
            "cancel_url": "checkout_cancel_url(base_url)",
            "line_items": """[
                {
                    'quantity': 1,
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': price_cents,
                        'recurring': {'interval': interval},
                        'product_data': {'name': PLAN_PRODUCT_NAME[tier]},
                    },
                }
            ]""",
            "metadata": "{'subscriber_id': str(subscriber_id), 'tier': tier}",
            "subscription_data": """{
                'metadata': {'subscriber_id': str(subscriber_id), 'tier': tier}
            }""",
        }
        self.assertEqual(set(self.kwargs), set(expected) | {"managed_payments"})
        for name, expression in expected.items():
            with self.subTest(argument=name):
                self.assertEqual(
                    ast.dump(self.kwargs[name]),
                    ast.dump(ast.parse(expression, mode="eval").body),
                )

    def test_real_sdk_encodes_explicit_false_for_both_actual_plans(self):
        self.assertEqual(len(PLAN_PRICE_CENTS), 2)
        self.assertEqual(set(PLAN_PRICE_CENTS), set(PLAN_INTERVAL))
        self.assertEqual(set(PLAN_PRICE_CENTS), set(PLAN_PRODUCT_NAME))
        for tier, amount in PLAN_PRICE_CENTS.items():
            with self.subTest(tier=tier):
                # Only evaluate the call-free inline price expression, never Checkout creation.
                expression = ast.Expression(body=self.kwargs["line_items"])
                self.assertFalse(
                    any(
                        isinstance(node, ast.Call)
                        for node in ast.walk(expression)
                    )
                )
                line_items = eval(
                    compile(expression, "<checkout-line-items>", "eval"),
                    {"__builtins__": {}},
                    {
                        "tier": tier,
                        "price_cents": amount,
                        "interval": PLAN_INTERVAL[tier],
                        "PLAN_PRODUCT_NAME": PLAN_PRODUCT_NAME,
                    },
                )
                payload = {
                    "mode": ast.literal_eval(self.kwargs["mode"]),
                    "managed_payments": ast.literal_eval(
                        self.kwargs["managed_payments"]
                    ),
                    "line_items": line_items,
                }
                encoded = dict(_api_encode(payload))
                self.assertEqual(encoded["managed_payments[enabled]"], "false")
                self.assertEqual(encoded["mode"], "subscription")
                prefix = "line_items[0][price_data]"
                self.assertEqual(encoded[f"{prefix}[currency]"], "usd")
                self.assertEqual(encoded[f"{prefix}[unit_amount]"], amount)
                self.assertEqual(
                    encoded[f"{prefix}[recurring][interval]"],
                    PLAN_INTERVAL[tier],
                )
                self.assertEqual(
                    encoded[f"{prefix}[product_data][name]"],
                    PLAN_PRODUCT_NAME[tier],
                )
                self.assertEqual(encoded["line_items[0][quantity]"], 1)
                self.assertFalse(
                    any(
                        "tax_code" in key or "automatic_tax" in key
                        for key in encoded
                    )
                )


if __name__ == "__main__":
    unittest.main()

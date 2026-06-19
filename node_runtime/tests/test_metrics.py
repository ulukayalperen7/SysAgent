import unittest

from sysagent_node.metrics import _percent, collect_metrics


class MetricsTest(unittest.TestCase):
    def test_percent_bounds_values(self):
        self.assertEqual(_percent(42.4), 42)
        self.assertEqual(_percent(42.6), 43)
        self.assertIsNone(_percent(-1))
        self.assertIsNone(_percent(101))
        self.assertIsNone(_percent("nope"))

    def test_collect_metrics_does_not_require_platform_specific_code(self):
        metrics = collect_metrics()
        self.assertIsInstance(metrics, dict)
        for value in metrics.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)


if __name__ == "__main__":
    unittest.main()

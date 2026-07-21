from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "src" / "audit_structure.py"
SPEC = importlib.util.spec_from_file_location("audit_structure", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

COMMON_MODULE_PATH = Path(__file__).parents[1] / "src" / "audit_common_forward.py"
COMMON_SPEC = importlib.util.spec_from_file_location(
    "audit_common_forward", COMMON_MODULE_PATH
)
COMMON_MODULE = importlib.util.module_from_spec(COMMON_SPEC)
assert COMMON_SPEC.loader is not None
COMMON_SPEC.loader.exec_module(COMMON_MODULE)


class LabelFreeSplitTests(unittest.TestCase):
    def test_straddling_event_is_purged_and_time_order_is_strict(self):
        frame = pd.DataFrame(
            {
                "source_row": range(8),
                "pump_index": [1, 1, 2, 2, 2, 3, 3, 3],
                "date": pd.to_datetime(
                    [
                        "2020-01-01",
                        "2020-01-02",
                        "2020-01-03",
                        "2020-01-05",
                        "2020-01-07",
                        "2020-01-08",
                        "2020-01-09",
                        "2020-01-10",
                    ]
                ),
            }
        )
        cutoff, groups, rows = MODULE.build_label_free_partition(frame, 0.5)
        assignment = groups.set_index("pump_index")["partition"].to_dict()
        self.assertEqual(assignment[1], "train")
        self.assertEqual(assignment[2], "purged")
        self.assertEqual(assignment[3], "test")
        self.assertLess(
            frame.loc[rows == "train", "date"].max(),
            frame.loc[rows == "test", "date"].min(),
        )
        self.assertEqual(cutoff, pd.Timestamp("2020-01-07"))

    def test_partition_rejects_label_column(self):
        frame = pd.DataFrame(
            {
                "source_row": [0, 1],
                "pump_index": [1, 2],
                "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "gt": [0, 1],
            }
        )
        with self.assertRaises(ValueError):
            MODULE.build_label_free_partition(frame, 0.5)

    def test_common_calendar_assignment_purges_straddling_event(self):
        groups = pd.DataFrame(
            {
                "pump_index": [1, 2, 3],
                "symbol": ["A", "B", "C"],
                "canonical_start": pd.to_datetime(
                    ["2020-01-01", "2020-01-04", "2020-01-08"]
                ),
                "canonical_end": pd.to_datetime(
                    ["2020-01-02", "2020-01-07", "2020-01-09"]
                ),
                "canonical_anchor": pd.to_datetime(
                    ["2020-01-01 12:00", "2020-01-05 12:00", "2020-01-08 12:00"]
                ),
            }
        )
        assigned = COMMON_MODULE.assign_groups(groups, pd.Timestamp("2020-01-06"))
        got = assigned.set_index("pump_index")["partition"].to_dict()
        self.assertEqual(got, {1: "train", 2: "purged", 3: "test"})


if __name__ == "__main__":
    unittest.main()

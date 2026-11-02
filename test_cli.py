import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from env_checker.cli import check_environment, load_config, main


class EnvironmentCheckerTests(unittest.TestCase):
    def test_success(self):
        config = {"required_env": [], "tools": []}
        report = check_environment(config)
        self.assertTrue(report["python"]["ok"])
        self.assertTrue(report["disk"]["ok"])
        self.assertTrue(report["overall_ok"])

    def test_missing_dependency_or_tool(self):
        report = check_environment({"required_env": [], "tools": ["tool_that_does_not_exist_xyz"]})
        self.assertFalse(report["developer_tools"]["tool_that_does_not_exist_xyz"])
        self.assertFalse(report["overall_ok"])

    def test_missing_environment_variable(self):
        with patch.dict(os.environ, {}, clear=True):
            report = check_environment({"required_env": ["ENV_CHECKER_TEST_MISSING"], "tools": []})
        self.assertFalse(report["environment_variables"]["ENV_CHECKER_TEST_MISSING"])
        self.assertFalse(report["overall_ok"])

    def test_malformed_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "bad.json"
            config_path.write_text("{ invalid json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(str(config_path))

    def test_invalid_configuration_path(self):
        with self.assertRaises(ValueError):
            load_config("this/path/should/not/exist/config.json")

    def test_cli_invalid_config_exit_code(self):
        self.assertEqual(main(["--config", "missing-config-file.json"]), 2)


if __name__ == "__main__":
    unittest.main()

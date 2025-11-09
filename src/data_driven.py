"""
Data-driven testing utilities.

This module provides utilities for separating test data from test logic,
enabling a single test to execute multiple variations from external data files.

This creates a "multiplier effect" - one test script can execute hundreds
of test cases by reading from data files.

Based on the comprehensive improvement blueprint for screen_automator.
"""

import csv
import json
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union


class DataFormat(Enum):
    """Supported data file formats."""

    JSON = "json"
    CSV = "csv"
    XML = "xml"


@dataclass
class TestDataRow:
    """
    Represents a single row of test data.

    This provides a consistent interface regardless of source format.
    """

    data: dict[str, Any]
    row_number: int
    source_file: str

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key with optional default."""
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access: row['username']"""
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator: 'username' in row"""
        return key in self.data


class DataProvider:
    """
    Loads test data from various file formats.

    This class provides a unified interface for reading test data from
    JSON, CSV, and XML files.

    Example:
        # Load test data
        provider = DataProvider("test_data/users.json")

        # Iterate over test cases
        for row in provider:
            username = row['username']
            password = row['password']
            # Run test with this data...
    """

    def __init__(self, file_path: Union[str, Path], format: Optional[DataFormat] = None):
        """
        Initialize data provider.

        Args:
            file_path: Path to data file
            format: Data format (auto-detected from extension if not specified)
        """
        self.file_path = Path(file_path)
        self.format = format or self._detect_format()
        self._data: Optional[list[dict[str, Any]]] = None

    def _detect_format(self) -> DataFormat:
        """Auto-detect format from file extension."""
        ext = self.file_path.suffix.lower()
        if ext == ".json":
            return DataFormat.JSON
        elif ext == ".csv":
            return DataFormat.CSV
        elif ext == ".xml":
            return DataFormat.XML
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def load(self) -> list[TestDataRow]:
        """
        Load all data from file.

        Returns:
            List of TestDataRow objects
        """
        if self._data is not None:
            # Already loaded, return cached data
            return [
                TestDataRow(data=row, row_number=i, source_file=str(self.file_path))
                for i, row in enumerate(self._data)
            ]

        if self.format == DataFormat.JSON:
            self._data = self._load_json()
        elif self.format == DataFormat.CSV:
            self._data = self._load_csv()
        elif self.format == DataFormat.XML:
            self._data = self._load_xml()

        return [
            TestDataRow(data=row, row_number=i, source_file=str(self.file_path))
            for i, row in enumerate(self._data)
        ]

    def _load_json(self) -> list[dict[str, Any]]:
        """Load JSON data file."""
        with open(self.file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Support both array of objects and single object
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If single object, wrap in list
            return [data]
        else:
            raise ValueError("JSON must be array of objects or single object")

    def _load_csv(self) -> list[dict[str, Any]]:
        """Load CSV data file."""
        with open(self.file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _load_xml(self) -> list[dict[str, Any]]:
        """
        Load XML data file.

        Expected format:
        <testdata>
            <testcase>
                <username>user1</username>
                <password>pass1</password>
            </testcase>
            <testcase>
                <username>user2</username>
                <password>pass2</password>
            </testcase>
        </testdata>
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        data = []
        for testcase in root:
            row = {}
            for element in testcase:
                row[element.tag] = element.text
            data.append(row)

        return data

    def __iter__(self) -> Iterator[TestDataRow]:
        """Allow iteration over data rows."""
        return iter(self.load())

    def __len__(self) -> int:
        """Get number of data rows."""
        return len(self.load())

    def __getitem__(self, index: int) -> TestDataRow:
        """Get specific row by index."""
        return self.load()[index]


class DataDrivenTest:
    """
    Base class for data-driven tests.

    This provides a structured way to write tests that execute multiple
    times with different data sets.

    Example:
        class LoginTest(DataDrivenTest):
            def __init__(self, automator):
                super().__init__(
                    data_file="test_data/login_cases.csv",
                    automator=automator
                )

            def run_test(self, data: TestDataRow):
                # This runs once for each row in the CSV
                username = data['username']
                password = data['password']
                expected_result = data['expected_result']

                login_page = LoginPage(self.automator)
                login_page.login(username, password)

                if expected_result == "success":
                    assert login_page.is_logged_in()
                else:
                    assert login_page.has_error_message()

        # Run all test cases
        test = LoginTest(automator)
        results = test.run_all()
    """

    def __init__(
        self, data_file: Union[str, Path], automator: Any, format: Optional[DataFormat] = None
    ):
        """
        Initialize data-driven test.

        Args:
            data_file: Path to data file
            automator: Automator instance
            format: Data format (auto-detected if not specified)
        """
        self.data_provider = DataProvider(data_file, format)
        self.automator = automator

    def run_test(self, data: TestDataRow):
        """
        Override this to implement test logic.

        This method is called once for each row in the data file.

        Args:
            data: Current test data row
        """
        raise NotImplementedError("Subclasses must implement run_test()")

    def setup(self):
        """
        Override this for setup that runs once before all tests.

        Example: Launch application, navigate to starting page.
        """
        pass

    def teardown(self):
        """
        Override this for teardown that runs once after all tests.

        Example: Close application, clean up files.
        """
        pass

    def setup_each(self, data: TestDataRow):
        """
        Override this for setup that runs before each test case.

        Args:
            data: Current test data row

        Example: Reset application state, clear form fields.
        """
        pass

    def teardown_each(self, data: TestDataRow):
        """
        Override this for teardown that runs after each test case.

        Args:
            data: Current test data row

        Example: Logout, save screenshots on failure.
        """
        pass

    def run_all(self) -> dict[str, Any]:
        """
        Run test for all data rows.

        Returns:
            Dictionary with test results:
            {
                'total': int,
                'passed': int,
                'failed': int,
                'errors': List[Dict]
            }
        """
        results = {"total": 0, "passed": 0, "failed": 0, "errors": []}

        self.setup()

        try:
            for row in self.data_provider:
                results["total"] += 1

                try:
                    self.setup_each(row)
                    self.run_test(row)
                    self.teardown_each(row)
                    results["passed"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(
                        {"row": row.row_number, "data": row.data, "error": str(e)}
                    )

        finally:
            self.teardown()

        return results


def parametrize(data_file: Union[str, Path], format: Optional[DataFormat] = None):
    """
    Decorator for parametrizing test functions with data files.

    This provides a pytest-style parametrize decorator for data-driven testing.

    Example:
        @parametrize("test_data/users.csv")
        def test_login(data, automator):
            username = data['username']
            password = data['password']

            login_page = LoginPage(automator)
            login_page.login(username, password)
            assert login_page.is_logged_in()

        # The test function will be called once for each row in users.csv
    """
    provider = DataProvider(data_file, format)

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            results = []
            for row in provider:
                try:
                    result = test_func(row, *args, **kwargs)
                    results.append(("pass", row.row_number, result))
                except Exception as e:
                    results.append(("fail", row.row_number, str(e)))
            return results

        return wrapper

    return decorator


class ConfigManager:
    """
    Manages configuration files for different environments.

    This allows tests to run in different environments (dev, staging, prod)
    without changing code.

    Example:
        # config/dev.json
        {
            "app_path": "C:/Program Files/MyApp/dev/app.exe",
            "api_url": "https://dev-api.example.com",
            "timeout": 5000
        }

        # config/prod.json
        {
            "app_path": "C:/Program Files/MyApp/app.exe",
            "api_url": "https://api.example.com",
            "timeout": 10000
        }

        # In test code
        config = ConfigManager("config/dev.json")
        app_path = config.get("app_path")
        timeout = config.get("timeout", default=30000)
    """

    def __init__(self, config_file: Union[str, Path], environment: Optional[str] = None):
        """
        Initialize config manager.

        Args:
            config_file: Path to config file
            environment: Optional environment name (dev, staging, prod)
        """
        self.config_file = Path(config_file)
        self.environment = environment
        self._config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, encoding="utf-8") as f:
            config = json.load(f)

        # If environment specified, look for environment-specific overrides
        if self.environment and self.environment in config:
            # Merge environment config over base config
            base_config = {k: v for k, v in config.items() if k != self.environment}
            env_config = config[self.environment]
            base_config.update(env_config)
            return base_config

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation: "database.host")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # Support dot notation for nested configs
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Config key not found: {key}")
        return value

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return self.get(key) is not None

    def to_dict(self) -> dict[str, Any]:
        """Get entire config as dictionary."""
        return self._config.copy()

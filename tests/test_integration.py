# Runs the integration tests (they need a .env file) and writes an HTML report to reports/integration_tests.html.
# Run it from the repo root:
#   python tests/test_integration.py
import os
import sys
import unittest

import HtmlTestRunner
from HtmlTestRunner.result import HtmlTestResult

# html-testRunner 1.2.1 calls a unittest helper newer Pythons don't have; without it, reporting crashes
if not hasattr(HtmlTestResult, '_count_relevant_tb_levels'):
    HtmlTestResult._count_relevant_tb_levels = lambda self, tb: 0

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    sys.path.insert(0, ROOT)
    test_suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, 'tests', 'integration_tests'))
    # A fixed report name: by default it's built from every test class's name, which is too long for a file
    runner = HtmlTestRunner.HTMLTestRunner(output=os.path.join(ROOT, 'reports'), report_name='integration_tests', add_timestamp=False,
                                           report_title='Integration Test Report', combine_reports=True)
    result = runner.run(test_suite)
    sys.exit(0 if result.wasSuccessful() else 1)

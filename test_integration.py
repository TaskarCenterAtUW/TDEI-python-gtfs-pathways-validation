import unittest
import HtmlTestRunner

# Define your test cases
from tests.integration_tests.test_gtfs_pathways_integration import TestGTFSPathwaysIntegration

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    # Add your test cases to the test suite
    test_suite.addTest(unittest.makeSuite(TestGTFSPathwaysIntegration))

    # Define the output file for the HTML report
    output_file = 'integration_test_report.html'

    # Open the output file in write mode
    with open(output_file, 'w') as f:
        # Create an HTMLTestRunner instance with the output file and customize the template
        runner = HtmlTestRunner.HTMLTestRunner(stream=f, report_title='Integration Test Report', combine_reports=True)

        # Run the test suite with the HTMLTestRunner
        runner.run(test_suite)

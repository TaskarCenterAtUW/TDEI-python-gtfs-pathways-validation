import unittest
import HtmlTestRunner

# Define your test cases
from tests.unit_tests.test_gtfs_pathways_serializer import TestGTFSPathwaysUpload, TestGTFSPathwaysUploadData, TestRequest, \
    TestMeta, TestResponse
from tests.unit_tests.test_pathways_feed_validation import TestSuccessPathwaysFeedValidation, TestFailurePathwaysFeedValidation
from tests.unit_tests.test_pathways_queue_worker import TestPathwaysQueueWorker
from tests.unit_tests.test_main import TestApp

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    # Add your test cases to the test suite
    test_suite.addTest(unittest.makeSuite(TestGTFSPathwaysUpload))
    test_suite.addTest(unittest.makeSuite(TestGTFSPathwaysUploadData))
    test_suite.addTest(unittest.makeSuite(TestRequest))
    test_suite.addTest(unittest.makeSuite(TestMeta))
    test_suite.addTest(unittest.makeSuite(TestResponse))
    test_suite.addTest(unittest.makeSuite(TestSuccessPathwaysFeedValidation))
    test_suite.addTest(unittest.makeSuite(TestFailurePathwaysFeedValidation))
    test_suite.addTest(unittest.makeSuite(TestPathwaysQueueWorker))
    test_suite.addTest(unittest.makeSuite(TestApp))

    # Define the output file for the HTML report
    output_file = 'test_report.html'

    # Open the output file in write mode
    with open(output_file, 'w') as f:
        # Create an HTMLTestRunner instance with the output file and customize the template
        runner = HtmlTestRunner.HTMLTestRunner(stream=f, report_title='Test Report', combine_reports=True)

        # Run the test suite with the HTMLTestRunner
        runner.run(test_suite)

# TDEI Python GTFS Pathways Validation Service Unit Test Cases

## Purpose


This document details the unit test cases for the [TDEI-python-gtfs-pathways-validation](https://github.com/TaskarCenterAtUW/TDEI-python-gtfs-pathways-validation)

------------

## Test Framework

Unit test cases are to be written using [Python Unittest](https://docs.python.org/3/library/unittest.html)

------------
## Test Cases


### Test cases table definitions 
- **Component** -> Specifies the code component 
- **Class Under Test** -> Target method name
- **Test Target** -> Specific requirement to test_ ex. Functional, security etc.
- **Scenario** -> Requirement to test
- **Expectation** -> Expected result from executed scenario

### Python unittest code pattern

```python
import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
```


### Test cases

| Component | Class Under Test | Test Target | Scenario | Expectation | Status |
|--|--|--|--|--|--|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload data | Expect to return same upload data |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload data_from | Expect to return same upload data_from |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload message | Expect to return same upload message |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload id | Expect to return same upload id |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload type | Expect to return same upload type |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload publish date | Expect to return same upload publish date |:white_check_mark:|
| Serializer | TestGTFSPathwaysUpload | Functional| When requested with upload to_json | Expect to return same dict |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with stage parameter| Expect to return stage |:white_check_mark:|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with tdei_project_group_id parameter| Expect to return tdei_project_group_id |:white_check_mark:|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with tdei_record_id parameter| Expect to return tdei_record_id |:white_check_mark:|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with user_id parameter| Expect to return user_id |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestRequest | Functional| When requested with tdei_project_group_id parameter| Expect to return tdei_project_group_id |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestMeta | Functional| When requested with file_upload_path parameter| Expect to return file_upload_path |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestResponse | Functional| When requested with response parameter| Expect to return either True or False |:white_check_mark:|
|--|--|--|--|--|--|
| Validation | TestSuccessPathwaysFeedValidation | Functional | When requested for validate function with the good (Baltimore Metro) feed | Expect to return False, failing only on tdei_level_change_same_level |:white_check_mark:|
| Validation | TestSuccessPathwaysFeedValidation | Functional | When requested for download_single_file function | Expect to download the file to local storage |:white_check_mark:|
| Validation | TestSuccessPathwaysFeedValidation | Functional | When requested for clean_up function with a file | Expect to remove the file |:white_check_mark:|
| Validation | TestSuccessPathwaysFeedValidation | Functional | When requested for clean_up function with a folder | Expect to remove the folder |:white_check_mark:|
| Validation | TestSuccessPathwaysFeedValidation | Functional | When requested for clean_up function with a path outside the downloads folder | Expect to leave it in place |:white_check_mark:|
|--|--|--|--|--|--|
| Validation | TestFailurePathwaysFeedValidation | Functional | When requested for validate function with a feed missing required files | Expect to return False |:white_check_mark:|
| Validation | TestFailurePathwaysFeedValidation | Functional | When requested for validate function with a file that isn't a zip | Expect to return False |:white_check_mark:|
| Validation | TestPathwaysFeedValidationOther | Functional | When the storage client fails or the file isn't found | Expect download_single_file to raise FeedDownloadError |:white_check_mark:|
| Validation | TestPathwaysFeedValidationOther | Functional | When the file isn't a .zip | Expect to return False without downloading |:white_check_mark:|
|--|--|--|--|--|--|
| Validation | TestPathwaysFeedValidationOther | Functional | When MobilityData reports any error | Expect to return False, with the errors as JSON |:white_check_mark:|
| Validation | TestPathwaysFeedValidationOther | Functional | When some errors are ones pathways_config.py downgrades | Expect the message to list only the others |:white_check_mark:|
| Validation | TestPathwaysFeedValidationOther | Functional | When every error is one pathways_config.py downgrades | Expect to return True |:white_check_mark:|
| Validation | TestPathwaysFeedValidationOther | Functional | When MobilityData's validator crashes | Expect the download folder to be removed |:white_check_mark:|
| Validation | TestGoodFile2 | Functional | When validating a good feed without pathways with the real validator | Expect to return True |:white_check_mark:|
| Validation | TestForeignKey | Functional | When validating a feed with a pathways error with the real validator | Expect to return False |:white_check_mark:|
|--|--|--|--|--|--|
| Report | TestNoticeOutcome | Functional | When judging an ERROR notice | Expect fails_upload only for pathways errors, unreadable feeds and missing files; error_not_pathways or downgraded_to_warning otherwise |:white_check_mark:|
| Report | TestValidationReport | Functional | When building a report | Expect every notice with its source and outcome, worst first, and a summary with counts by outcome |:white_check_mark:|
| Report | TestValidationReport | Functional | When rendering and zipping the report | Expect escaped HTML, and a zip with report.json, report.html and MobilityData's own reports |:white_check_mark:|
| Report | TestMakeNotice | Functional | When a TDEI check finds problems | Expect a notice in MobilityData's format with a few samples and the total; none when nothing was found |:white_check_mark:|
| Report | TestGtfsFeed | Functional | When reading a feed | Expect stops, pathways and levels with row numbers, including from a folder in the zip or with a byte order mark |:white_check_mark:|
| Report | TestValidationWithCustomChecksAndReport | Functional | When TDEI's checks report warnings or errors | Expect warnings to pass and errors to fail the upload |:white_check_mark:|
| Report | TestValidationWithCustomChecksAndReport | Functional | When TDEI's checks crash | Expect validation to carry on without them |:white_check_mark:|
| Report | TestValidationWithCustomChecksAndReport | Functional | When uploading the report | Expect it next to the feed with its own name, and validation to carry on if the upload fails |:white_check_mark:|
|--|--|--|--|--|--|
| MobilityData | TestMobilityDataResult | Functional | When reading a validator report | Expect ERROR notices as errors, and status True when there are none |:white_check_mark:|
| MobilityData | TestMobilityDataValidator | Functional | When the validator jar is missing, can't run or writes no report | Expect MobilityDataValidatorError |:white_check_mark:|
| MobilityData | TestMobilityDataValidator | Functional | When the validator can't load the feed | Expect its system errors as feed errors, marked feedUnreadable |:white_check_mark:|
| MobilityData | TestMobilityDataValidator | Functional | When a validator rule crashes on a feed it loaded | Expect the system error to be logged only |:white_check_mark:|
| MobilityData | TestMobilityDataValidatorJar | Functional | When running the real validator jar | Expect a feed's errors, each run in its own folder, and i_o_error for a file that isn't a zip |:white_check_mark:|
|--|--|--|--|--|--|
| TDEI checks | TestStandardStation | Functional | When checking the standard test station (entrance, concourse, two platforms, ramp, stairs, elevators, one-way escalator) | Expect no notices |:white_check_mark:|
| TDEI checks | TestStandardStation | Functional | When a check crashes | Expect it to be logged and skipped, and the other checks to run |:white_check_mark:|
| TDEI checks | TestPathwayChecks | Functional | When a pathway is wrong: an escalator, elevator or stairs on one level, walkway changing level without a slope, stair_count the wrong way, length too short or long, speed far off, ends too far apart for its mode, or a duplicate | Expect that pathway flagged, and close cases (same-height levels, stair_count 0, short lengths, side-by-side routes) not flagged |:white_check_mark:|
| TDEI checks | TestLevelChecks | Functional | When a level is wrong: a boarding area off its platform's level, an unreachable or unused level, a repeated or far-off level_index, a stop far from its level, or a missing level_id | Expect that level or stop flagged |:white_check_mark:|
| TDEI checks | TestStationChecks | Functional | When a station with pathways has no entrance, a stop no pathway touches, or a stop far from its station | Expect the station or stop flagged |:white_check_mark:|
| TDEI checks | TestRouteChecks | Functional | When an entrance reaches no platform, or no platform step-free; a platform has no step-free way in or out, or only by elevator; or two platforms have no step-free transfer | Expect that entrance or platform flagged, and platforms joined only through entrances skipped |:white_check_mark:|
| TDEI checks | TestEntranceChecks | Functional | When an entrance has no coordinates, or isn't at street level | Expect the entrance flagged |:white_check_mark:|
| TDEI checks | TestMetrics | Functional | When measuring the standard station, or it without step-free routes | Expect completeness and connectivity counts and percentages |:white_check_mark:|
| TDEI checks | TestMetrics | Functional | When measuring a feed without pathways | Expect percentages of None where nothing is counted |:white_check_mark:|
| Report | TestValidationReport, TestValidationWithCustomChecksAndReport | Functional | When the feed is measured, or measuring crashes | Expect metrics in the summary and HTML, or null without blocking the upload |:white_check_mark:|
| One-way service | TestOneWayService | Functional | When trips only end, or only start, at a platform (or pickup_type / drop_off_type say so) | Expect it to be arrival-only, or departure-only |:white_check_mark:|
| One-way service | TestOneWayService | Functional | When MobilityData finds places unreachable one way that match their platform's service, including nodes on the routes | Expect them downgraded to warnings, and the rest (wrong way, through platforms, cut off both ways, unsampled) still failing |:white_check_mark:|
|--|--|--|--|--|--|
| Queue worker | TestPathwaysQueueWorker | Functional | When a message arrives | Expect it to be read and processed |:white_check_mark:|
| Queue worker | TestPathwaysQueueWorker | Functional | When processing a message with a file path | Expect the feed validated and the result published |:white_check_mark:|
| Queue worker | TestPathwaysQueueWorker | Functional | When processing a message with no file path, or validation raises | Expect a failure published with the reason |:white_check_mark:|
| Queue worker | TestPathwaysQueueWorker | Functional | When publishing the result | Expect the report URL and summary when there is a report, and nulls when there isn't |:white_check_mark:|
| Queue worker | TestPathwaysQueueWorker | Functional | When stopping | Expect the listening thread to be joined |:white_check_mark:|
|--|--|--|--|--|--|
| Server | TestApp | Functional | When calling get_settings function | Expect to return env variables |:white_check_mark:|
| Server | TestApp | Functional | When calling ping function | Expect to return 200 |:white_check_mark:|
| Server | TestApp | Functional | When calling root function | Expect to return 200 |:white_check_mark:|


## Integration Test cases
In case of integration tests, the system will look for all the integration points to be tested

| Component | Feature under test | Scenario | Expectation | Status |
|-|-|-|-|-|
| Pathways Validator | Servicebus integration | Subscribe to upload topic to verify servicebus integration | Expect to return message |:white_check_mark: |
| Pathways Validator | Servicebus integration | Should publish a message to be received on topic | Expect to receive message on target topic | :white_check_mark: |
| Pathways Validator | Storage Integration | Fetching a file returns a file entity | Expect to return the file entity | |


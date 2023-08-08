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
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with tdei_org_id parameter| Expect to return tdei_org_id |:white_check_mark:|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with tdei_record_id parameter| Expect to return tdei_record_id |:white_check_mark:|
| Serializer | TestGTFSPathwaysUploadData | Functional| When requested with user_id parameter| Expect to return user_id |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestRequest | Functional| When requested with tdei_org_id parameter| Expect to return tdei_org_id |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestMeta | Functional| When requested with file_upload_path parameter| Expect to return file_upload_path |:white_check_mark:|
|--|--|--|--|--|--|
| Serializer | TestResponse | Functional| When requested with response parameter| Expect to return either True or False |:white_check_mark:|
|--|--|--|--|--|--|
| Validation | TestSuccessGTFSPathwaysValidation | Functional| When requested for clean_up_file function| Expect to return remove files from local storage |:white_check_mark:|
| Validation | TestSuccessGTFSPathwaysValidation | Functional| When requested for clean_up_folder function| Expect to return remove directory from local storage |:white_check_mark:|
| Validation | TestSuccessGTFSPathwaysValidation | Functional| When requested for download_single_file function| Expect to download file in local storage |:white_check_mark:|
| Validation | TestSuccessGTFSPathwaysValidation | Functional| When requested for is_gtfs_pathways_valid function| Expect to return True |:white_check_mark:|
| Validation | TestSuccessGTFSPathwaysValidation | Functional| When requested for validate function| Expect to return True |:white_check_mark:|
|--|--|--|--|--|--|
| Validation | TestFailureGTFSPathwaysValidation | Functional| When requested for download_single_file function with invalid endpoint| Expect to throw exception |:white_check_mark:|
| Validation | TestFailureGTFSPathwaysValidation | Functional| When requested for is_gtfs_pathways_valid function with invalid file format| Expect to return False |:white_check_mark:|
| Validation | TestFailureGTFSPathwaysValidation | Functional| When requested for is_gtfs_pathways_valid function with invalid zip file| Expect to return False |:white_check_mark:|
| Validation | TestFailureGTFSPathwaysValidation | Functional| When requested for validate function with invalid file| Expect to return False |:white_check_mark:|
|--|--|--|--|--|--|
| Validator | TestGTFSPathwaysValidator | Functional| When calling send_status function with invalid parameters| Expect to return invalid parameters |:white_check_mark:|
| Validator | TestGTFSPathwaysValidator | Functional| When calling subscribe function | Expect to return a message |:white_check_mark:|
| Validator | TestGTFSPathwaysValidator | Functional| When calling send_status function with invalid parameters | Expect to return a valid message |:white_check_mark:|
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


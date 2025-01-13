import unittest
from v2_utils import remove_unmatched_tags
from app import app
import json, random,os
from dotenv import load_dotenv

load_dotenv()

class CustomTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"{test._testMethodName} - passed")

class CustomTestRunner(unittest.TextTestRunner):
    resultclass = CustomTestResult

    def run(self, test):
        result = super().run(test)
        if result.wasSuccessful():
            print("All Testcases Passed")
        return result


class TestRemoveUnmatchedTags(unittest.TestCase):
    """
    Static test case input & output for check markdown handler function
    """
    def test_remove_unmatched_tags_basic(self):
        input_text = "<div>Test content</p></div>"
        expected_output = "<ul><div>Test content</div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)
    
    def test_remove_unmatched_tags_unmatched_opening(self):
        input_text = "<div>Test content"
        expected_output = "<ul><div>Test content</div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)
    
    def test_remove_unmatched_tags_unmatched_closing(self):
        input_text = "<div><span><p>Test content</div>"
        expected_output = "<ul><div><span><p>Test content</p></span></div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)
    
    def test_remove_unmatched_tags_nested_tags(self):
        input_text = "<div><p>Test content</p></p></div>"
        expected_output = "<ul><div><p>Test content</p></div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)

    def test_remove_unmatched_tags_unmatched_nested_opening(self):
        input_text = "<div><p>Test content</div>"
        expected_output = "<ul><div><p>Test content</p></div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)
    
    def test_remove_unmatched_tags_unmatched_nested_closing(self):
        input_text = "<div>Test content</p></div>"
        expected_output = "<ul><div>Test content</div></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)

    def test_remove_unmatched_tags_multiple_unmatched_tags(self):
        input_text = "<div>Test</div><p>Content</p><span>Here"
        expected_output = "<ul><div>Test</div><p>Content</p><span>Here</span></ul>"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)

    def test_remove_unmatched_tags_text_with_no_tags(self):
        input_text = "Plain text with no tags"
        expected_output = "Plain text with no tags"
        self.assertEqual(remove_unmatched_tags(input_text), expected_output)
    
    def test_remove_unmatched_tags_empty_string(self):
        input_text = ""
        expected_output = ""
        self.assertEqual(len(remove_unmatched_tags(input_text)), len(expected_output))
        

class TestIssuesEndpoints(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.issues_data = None  # To store issues data for use in subsequent tests
        self.headers = {
            'x-secret-key':os.getenv('SECRET_KEY')
        }
        
        # Fetch issues data during setup
        self._fetch_issues_data()
    
    def _fetch_issues_data(self):
        # Validate the /issues endpoint and store the issues data
        response = self.app.get('/issues',headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.issues_data = data.get('issues', [])
        self.assertTrue(len(self.issues_data) > 0, "No issues found in response")

    def test_get_issues_success(self):
        # Check if issues data is correctly fetched
        self.assertIsNotNone(self.issues_data, "Issues data is not populated")
    
    def test_get_issues_detail_success(self):
        # Ensure the /issues endpoint was successfully called and issues data is available
        if not self.issues_data:
            self.skipTest("Skipping detail test as /issues endpoint did not return data")
        
        # Use first data from /issues response to form the endpoint URL
        
        index = random.randrange(1, len(self.issues_data) - 1)
        sample_issue = self.issues_data[index]['issues'][0]
        issue_id = sample_issue['id']
        orgname = self.issues_data[index]['org_name']
        
        endpoint = f'/v2/issues/{orgname}/{issue_id}'
        
        response = self.app.get(endpoint,headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    def test_get_repo_detail_success(self):
        # Ensure the /issues endpoint was successfully called and issues data is available
        if not self.issues_data:
            self.skipTest("Skipping detail test as /issues endpoint did not return data")
        
        # Use first data from /issues response to form the endpoint URL
        index = random.randrange(1, len(self.issues_data) - 1)
        orgname = self.issues_data[index]['org_name']
        endpoint = f'/issues/{orgname}'        
        response = self.app.get(endpoint,headers=self.headers)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main(testRunner=CustomTestRunner())

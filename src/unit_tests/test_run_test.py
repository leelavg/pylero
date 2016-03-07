'''
Created on Apr 19, 2015

@author: szacks
'''
import unittest2
import datetime
import os
from pylarion.test_run import TestRun
from pylarion.exceptions import PylarionLibException
from pylarion.test_record import TestRecord
from pylarion.work_item import TestCase
from pylarion.plan import Plan

DEFAULT_PROJ = TestRun.default_project
TEMPLATE_ID = "tmp_regr-%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%s")
TEST_RUN_ID = "tr_regr-%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%s")
PLAN_ID = "plan_regr-%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%s")
CUR_PATH = os.path.dirname(os.path.abspath(__file__))
ATTACH_PATH = CUR_PATH + "/refs/red_box.png"
ATTACH_TITLE = "File"


class TestRunTest(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        tc1 = TestCase.create(DEFAULT_PROJ,
                              "regression",
                              "regression",
                              caseimportance="high",
                              caselevel="component",
                              caseautomation="notautomated",
                              caseposneg="positive",
                              testtype="functional",
                              subtype1="-")
        cls.NEW_TEST_CASE = tc1.work_item_id
        tc2 = TestCase.create(DEFAULT_PROJ,
                              "regression",
                              "regression",
                              caseimportance="high",
                              caselevel="component",
                              caseautomation="notautomated",
                              caseposneg="positive",
                              testtype="functional",
                              subtype1="-")
        cls.NEW_TEST_CASE2 = tc2.work_item_id
        Plan.create(plan_id=PLAN_ID,
                    plan_name="regression",
                    project_id=DEFAULT_PROJ,
                    parent_id=None,
                    template_id="release")
        cls.NEW_PLAN = PLAN_ID

    def test_001_create_template(self):
        """This test does the following:
        * Creates a TestRun template based on the "Empty" template
        * Verifies that the returned object exists and is a template
        * Adds a custom field as a kwarg
        * Tries to create another template with an invalid enum value in kwarg
        * Tries to create another template with an invalid kwarg
        """
        template = TestRun.create_template(
            DEFAULT_PROJ, TEMPLATE_ID, "Empty", arch="i386")
        self.assertIsNotNone(template.test_run_id)
        self.assertTrue(template.is_template)
        self.assertEqual(template.arch, "i386")
        with self.assertRaises(PylarionLibException):
            template = TestRun.create_template(
                DEFAULT_PROJ, TEMPLATE_ID + "1", "Empty", arch="BAD")
        with self.assertRaises(PylarionLibException):
            template = TestRun.create_template(
                DEFAULT_PROJ, TEMPLATE_ID + "2", "Empty", notaparm="BAD")

    def test_002_create_run(self):
        """This test does the following:
        * creates a test riun based on the template created in previous test
        * Verifies that the returned object exists and is not a template
        """
        tr = TestRun.create(DEFAULT_PROJ, TEST_RUN_ID, TEMPLATE_ID)
        self.assertIsNotNone(tr.test_run_id)
        self.assertFalse(tr.is_template)

    def test_003_get(self):
        """This test does the following:
        * Verifies error with invalid test_run_id
        * Gets a valid TestRun
        * verifies that the TestRun retrieves has the expected test_run_id
        """
        with self.assertRaises(PylarionLibException):
            TestRun(project_id=DEFAULT_PROJ, test_run_id="InValid")
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        self.assertEqual(tr.test_run_id, TEST_RUN_ID)

    def test_004_search(self):
        """This test does the following:
        * Gets a TestRun
        * Searches using the same query as the testrun (adding project id)
        * verifies that there are number of records returned as are in the
          records attribute of the TestRun
        """
        query = "id:%s" % (TEST_RUN_ID)
        lst_tr = TestRun.search(query)
        self.assertEqual(lst_tr[0].test_run_id, TEST_RUN_ID)

    def test_005_test_record_by_fields(self):
        """This test does the following:
        * gets a TestRun object
        * Adds a TestRecord to it
        ** verifies that it fails with an invalid result
        ** verifies that it fails if it adds a duplicate case.
        * Adds an attachment to the record.
        ** verifies that the attachment is there
        * deletes the attachment
        ** verifies the attachment is not there
        * updates the test record.
        """
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        with self.assertRaises(PylarionLibException):
            tr.add_test_record_by_fields(
                self.NEW_TEST_CASE, "invalid", "No Comment",
                tr.logged_in_user_id, datetime.datetime.now(), "50.5")
        tr.add_test_record_by_fields(
            self.NEW_TEST_CASE, "passed", "No Comment", tr.logged_in_user_id,
            datetime.datetime.now(), "50.5")
        tr.reload()
        self.assertEqual(tr.status, "finished")
        # test that the same case cannot be added multiple times.
        with self.assertRaises(PylarionLibException):
            tr.add_test_record_by_fields(
                self.NEW_TEST_CASE, "passed", "No Comment",
                tr.logged_in_user_id, datetime.datetime.now(), "50.5")
        tr.reload()
        rec = tr.records[-1]
        tr.add_attachment_to_test_record(
            rec.test_case_id, ATTACH_PATH, ATTACH_TITLE)
        tr.reload()
        rec = tr.records[-1]
        self.assertTrue(len(rec.attachments) == 1)
        self.assertEqual(rec.attachments[0].title, ATTACH_TITLE)
        tr.delete_attachment_from_test_record(rec.test_case_id,
                                              rec.attachments[0].filename)
        tr.reload()
        rec = tr.records[-1]
        self.assertEqual(rec.attachments, [])
        tr.update_test_record_by_fields(rec.test_case_id,
                                        rec.result,
                                        "Yes Comment",
                                        rec.executed_by,
                                        rec.executed,
                                        rec.duration)
        tr.reload()
        rec = tr.records[-1]
        self.assertEqual(rec.comment, "Yes Comment")

    def test_006_test_record_by_object(self):
        """This test does the following:
        * gets a TestRun
        * creates a TestRecord
        * populates the TestRecord
        * Tries to add a duplicate TestRecord (should fail)
        * Adds a TestRecord
        * Reloads the TestRun
        * Verifies the TestRecord was added
        * Updates the TestRecord
        * Reloads the TestRun
        * Verifies the TestRecord was modified
        """
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        rec = TestRecord()
        rec.test_case_id = self.NEW_TEST_CASE
        rec.comment = "No Comment"
        rec.duration = "50.5"
        # verify that it does not allow duplicate records.
        # (same record was added in previous test)
        with self.assertRaises(PylarionLibException):
            tr.add_test_record_by_object(rec)
        rec.test_case_id = self.NEW_TEST_CASE2
        tr.add_test_record_by_object(rec)
        tr.reload()
        check_rec = tr.records[-1]
        self.assertEqual(tr.status, "inprogress")
        self.assertEqual(check_rec.test_case_id, self.NEW_TEST_CASE2)
        rec.result = "blocked"
        rec.executed_by = tr.logged_in_user_id
        rec.executed = datetime.datetime.now()
        tr.update_test_record_by_object(self.NEW_TEST_CASE2, rec)
        tr.reload()
        self.assertEqual(tr.status, "finished")

        check_rec = tr.records[-1]
        self.assertEqual(check_rec.result, "blocked")

    def test_007_attachment(self):
        """This test does the following:
        * add an attachment to the TestRun.
        * verify that there is 1 attachment with the correct title
        * verify the get_attachment function
        * verify the get_attachments function
        * delete the attachment
        * verify that there are no attachments.
        """
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        tr.add_attachment(ATTACH_PATH, ATTACH_TITLE)
        tr.reload()
        self.assertEqual(len(tr.attachments), 1)
        self.assertEqual(tr.attachments[0].title, ATTACH_TITLE)
        attach = tr.get_attachment(tr.attachments[0].filename)
        self.assertEqual(tr.attachments[0].title, attach.title)
        lst_attach = tr.get_attachments()
        self.assertEqual(lst_attach[0].title, attach.title)
        tr.delete_attachment(tr.attachments[0].filename)
        tr.reload()
        self.assertEqual(tr.attachments, [])

    def test_008_update(self):
        """This test does the following:
        * gets a TestRun
        * modifies an attribute
        * updates the TestRun
        * reloads the TestRun
        * verifies that the TestRun attribute has changed
        """
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        tr.type = "featureverification"
        tr.update()
        tr.reload()
        self.assertEqual(tr.type, "featureverification")

    def test_009_dynamic_records(self):
        """This test does the following:
        * creates a TestRun based on the Example template (Dynamic query)
        * verifies that it is a dynamic query
        * updates an test record.
        * reloads
        * verifies that the record has been added
        """
        tr = TestRun.create("pylarion", "querytest", "Example")
        self.assertEquals(tr.select_test_cases_by, "dynamicQueryResult")
        num_recs = len(tr.records)
        test_case_id = tr.records[0].test_case_id
        tr.update_test_record_by_fields(test_case_id, "blocked", "comment",
                                        tr.logged_in_user_id,
                                        datetime.datetime.now(), 0)
        tr.reload()
        self.assertEquals(num_recs, len(tr.records))
        self.assertEquals(test_case_id, tr.records[0].test_case_id)
        self.assertEquals(tr.records[0].result, "blocked")

    def test_010_customfield_object(self):
        """This test does the following:
        * gets a TestRun
        * Adds a Plan to it
        * Verifies that the plan was added
        * Verifies that a non valid plan cant be added
        """
        tr = TestRun(project_id=DEFAULT_PROJ, test_run_id=TEST_RUN_ID)
        with self.assertRaises(PylarionLibException):
            tr.plannedin = "not_valid"
        tr.plannedin = self.NEW_PLAN
        self.assertEquals(tr.plannedin, self.NEW_PLAN)
        tr.update()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest2.main()

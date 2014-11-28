#!/usr/bin/env python
# -*- coding: utf8 -*-

# A temporary, just-show-something-thing before proper testing code arises.

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import random
import unittest

from pylarionlib.server import Server
from pylarionlib.test_classes import FunctionalTestCase, StructuralTestCase, NonFunctionalTestCase, TestSuite
from pylarionlib.document import Document
from pylarionlib.simple_test_plan import SimpleTestPlan
from pylarionlib.test_run import TestRun
from pylarionlib.simple_test_run import SimpleTestRun
from pylarionlib.tracker_text import TrackerText

my_login = 'vkadlcik'
my_password = '94rskco.kftg9'
my_project_name = 'BrnoTraining'
my_server = Server('http://polarion.dqe.lab.eng.bos.redhat.com/polarion', my_login, my_password, my_project_name)


class TestWorkItemCRUD(unittest.TestCase):
 
    test_session = None
 
    @classmethod
    def setUpClass(cls):
        super(TestWorkItemCRUD, cls).setUpClass()
        TestWorkItemCRUD.test_session = my_server._createSession()
        TestWorkItemCRUD.test_session._login()
 
    @classmethod
    def tearDownClass(cls):
        TestWorkItemCRUD.test_session._logout()
        super(TestWorkItemCRUD, cls).tearDownClass()
 
    def test_0001(self):
        permanent_title = 'vaskovo uzitkovy test 1'
        tc = FunctionalTestCase(TestWorkItemCRUD.test_session)
        tc.title = permanent_title
        tc._crudCreate()
        self.assertTrue(tc.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(permanent_title, tc.title)
        tc.title = 'tajna zmena v titulku!'
        self.assertNotEqual(permanent_title, tc.title)
        tc._crudRetrieve()
        self.assertEqual(permanent_title, tc.title)
 
    def test_0002(self):
        old_title = 'vaskovo stavebni test 1'
        new_title = 'zmena v titulku!'
        tc = StructuralTestCase(TestWorkItemCRUD.test_session)
        tc.title = old_title
        tc._crudCreate()
        self.assertTrue(tc.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(old_title, tc.title)
        tc.title = new_title
        self.assertEqual(new_title, tc.title)
        tc._crudUpdate()
        self.assertEqual(new_title, tc.title)
        tc._crudRetrieve()
        self.assertEqual(new_title, tc.title)
 
    def test_0003(self):
        title = 'vaskovo neuzitkovy test 1'
        tc1 = NonFunctionalTestCase(TestWorkItemCRUD.test_session)
        tc1.title = title
        tc1._crudCreate()
        self.assertTrue(tc1.puri.startswith('subterra:data-service:objects:'))
        pid = tc1.pid
        tc2 = TestWorkItemCRUD.test_session.getWorkItemByPID(pid)
        self.assertEqual(title, tc2.title)
        self.assertIsInstance(tc2, NonFunctionalTestCase)
        self.assertEqual(tc1.title, tc2.title)
 
    def test_0004(self):
        tc1 = TestSuite(TestWorkItemCRUD.test_session)
        tc1.title = 'vaskovo testovy pruvod'
        tc1._crudCreate()
        tc2 = TestWorkItemCRUD.test_session.getWorkItemByPURI(tc1.puri)
        self.assertEqual(tc1.puri, tc2.puri)
        self.assertEqual(tc1.pid, tc2.pid)
        self.assertEqual(tc1.__class__, tc2.__class__)
 
 
class TestDocumentCRUD(unittest.TestCase):
 
    test_session = None
 
    @classmethod
    def setUpClass(cls):
        super(TestDocumentCRUD, cls).setUpClass()
        TestDocumentCRUD.test_session = my_server._createSession()
        TestDocumentCRUD.test_session._login()
 
    @classmethod
    def tearDownClass(cls):
        TestDocumentCRUD.test_session._logout()
        super(TestDocumentCRUD, cls).tearDownClass()
 
    def test_0001(self):
 
        space = 'vkadlcik_spejs'
        name = 'vaskovo dokument'
 
        old = TestDocumentCRUD.test_session.getDocumentByPID(name, namespace=space)
        if old:
            old._crudDelete()
 
        permanent_name = name
 
        doc = Document(TestDocumentCRUD.test_session)
        doc.namespace = space
        doc.structureLinkRole = 'parent'
        doc.name = permanent_name
        doc.workItemTypes = [ 'functionaltestcase', 'unittestcase' ]
        doc.text = TrackerText(TestDocumentCRUD.test_session, 'text/html', 'cokoliv', False)
 
        doc._crudCreate()
 
        self.assertTrue(doc.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(permanent_name, doc.name)
        doc.name = 'tajna zmena v titulku!'
        self.assertNotEqual(permanent_name, doc.name)
 
        doc._crudRetrieve()
 
        self.assertEqual(permanent_name, doc.name)
 
        newContent = 'It is a tale - Told by an idiot, full of sound and fury - Signifying nothing.'
        self.assertNotEqual(newContent, doc.text.content)
        doc.text.content = newContent
 
        doc._crudUpdate()
 
        self.assertEqual(newContent, doc.text.content)
 
        refreshed = TestDocumentCRUD.test_session.getDocumentByPURI(doc.puri)
        self.assertEqual(newContent, refreshed.text.content)
 
        refreshed._crudDelete()
 
        self.assertIsNone(refreshed.puri)
        self.assertIsNone(TestDocumentCRUD.test_session.getDocumentByPURI(doc.puri))
 
 
class TestSimpleTestPlanCRUD(unittest.TestCase):
 
    test_session = None
 
    @classmethod
    def setUpClass(cls):
        super(TestSimpleTestPlanCRUD, cls).setUpClass()
        TestSimpleTestPlanCRUD.test_session = my_server._createSession()
        TestSimpleTestPlanCRUD.test_session._login()
 
    @classmethod
    def tearDownClass(cls):
        TestSimpleTestPlanCRUD.test_session._logout()
        super(TestSimpleTestPlanCRUD, cls).tearDownClass()
 
    def test_0001(self):
 
        space = 'vkadlcik_spejs'
        name = 'vaskovo dokument'
 
        old = TestSimpleTestPlanCRUD.test_session.getDocumentByPID(name, namespace=space)
        if old:
            old._crudDelete()
 
        permanent_name = name
 
        doc = SimpleTestPlan(TestSimpleTestPlanCRUD.test_session)
        doc.namespace = space
        doc.structureLinkRole = 'parent'
        doc.name = permanent_name
        doc.text = TrackerText(TestSimpleTestPlanCRUD.test_session, 'text/html', 'cokoliv', False)
 
        doc._crudCreate()
 
        self.assertTrue(doc.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(permanent_name, doc.name)
        doc.name = 'tajna zmena v titulku!'
        self.assertNotEqual(permanent_name, doc.name)
 
        doc._crudRetrieve()
 
        self.assertEqual(permanent_name, doc.name)
 
        newContent = 'It is a tale - Told by an idiot, full of sound and fury - Signifying nothing.'
        self.assertNotEqual(newContent, doc.text.content)
        doc.text.content = newContent
 
        doc._crudUpdate()
 
        self.assertEqual(newContent, doc.text.content)
 
        refreshed = TestSimpleTestPlanCRUD.test_session.getSimpleTestPlanByPURI(doc.puri)
        self.assertEqual(newContent, refreshed.text.content)
 
        refreshed._crudDelete()
 
        self.assertIsNone(refreshed.puri)
        self.assertIsNone(TestSimpleTestPlanCRUD.test_session.getSimpleTestPlanByPURI(doc.puri))

                
def _gen_run_id(cls):
    # TODO: make this function not so lame
    _gen_run_id.counter += 1
    return '{}_{}_{}_{}'.format(
                                      cls.test_session._server.login,
                                      datetime.datetime.now().strftime('%Y-%m-%d__%H_%M_%S'),
                                      _gen_run_id.counter,
                                      random.random()
                                      ).replace('.', '')
_gen_run_id.counter = 0


class TestTestRunCRUD(unittest.TestCase):

    test_session = None

    @classmethod
    def setUpClass(cls):
        super(TestTestRunCRUD, cls).setUpClass()
        TestTestRunCRUD.test_session = my_server._createSession()
        TestTestRunCRUD.test_session._login()

    @classmethod
    def tearDownClass(cls):
        TestTestRunCRUD.test_session._logout()
        super(TestTestRunCRUD, cls).tearDownClass()

    def test_0001(self):

        permanent_status = TestRun.Status.IN_PROGRESS

        testRun = TestRun(TestTestRunCRUD.test_session)
        testRun.pid = _gen_run_id(TestTestRunCRUD)
        testRun.status = permanent_status

        testRun._crudCreate()

        self.assertTrue(testRun.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(permanent_status, testRun.status)
        testRun.status = TestRun.Status.FINISHED
        self.assertNotEqual(permanent_status, testRun.status)

        testRun._crudRetrieve()

        self.assertEqual(permanent_status, testRun.status)

        new_status = _gen_run_id(TestTestRunCRUD)
        self.assertNotEqual(new_status, testRun.status)
        testRun.status = new_status

        testRun._crudUpdate()

        self.assertEqual(new_status, testRun.status)

        refreshed = TestTestRunCRUD.test_session.getTestRunByPURI(testRun.puri)
        self.assertEqual(new_status, refreshed.status)


class TestSimpleTestRunCRUD(unittest.TestCase):
 
    test_session = None
 
    @classmethod
    def setUpClass(cls):
        super(TestSimpleTestRunCRUD, cls).setUpClass()
        TestSimpleTestRunCRUD.test_session = my_server._createSession()
        TestSimpleTestRunCRUD.test_session._login()
 
    @classmethod
    def tearDownClass(cls):
        TestSimpleTestRunCRUD.test_session._logout()
        super(TestSimpleTestRunCRUD, cls).tearDownClass()
 
    def test_0001(self):
 
        permanent_status = SimpleTestRun.Status.NOT_RUN

        simpleTestRun = SimpleTestRun(TestSimpleTestRunCRUD.test_session)
        simpleTestRun.pid = _gen_run_id(TestSimpleTestRunCRUD)
        simpleTestRun.status = permanent_status

        simpleTestRun._crudCreate()

        self.assertTrue(simpleTestRun.puri.startswith('subterra:data-service:objects:'))
        self.assertEqual(permanent_status, simpleTestRun.status)
        simpleTestRun.status = SimpleTestRun.Status.FINISHED
        self.assertNotEqual(permanent_status, simpleTestRun.status)

        simpleTestRun._crudRetrieve()

        self.assertEqual(permanent_status, simpleTestRun.status)

        new_status = _gen_run_id(TestSimpleTestRunCRUD)
        self.assertNotEqual(new_status, simpleTestRun.status)
        simpleTestRun.status = new_status

        simpleTestRun._crudUpdate()

        self.assertEqual(new_status, simpleTestRun.status)

        refreshed = TestSimpleTestRunCRUD.test_session.getTestRunByPURI(simpleTestRun.puri)
        self.assertEqual(new_status, refreshed.status)

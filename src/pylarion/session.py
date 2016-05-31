# -*- coding: utf8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import logging
import time
import suds.sax.element
import ssl
import os
from urlparse import urlparse

from suds.plugin import MessagePlugin
from suds.sax.attribute import Attribute


# TODO: figure out what this does
logger = logging.getLogger(__name__)


# the reason why this function definition is at the top is because it is
# assigned to "ssl._create_default_https_context", few lines below
def create_redhat_ssl_context():
    """this function creates a custom ssl context which is required for ssl
    connection in python-version >=2.7.10. this ssl context is customize to use
    redhat certificate which is located in 'cert_path'.
    """
    cert_path = os.path.join('/etc', 'pylarion', 'newca.crt')
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_verify_locations(cert_path)
    return context


# this line tells python >= 2.7.10 to use 'redhat_ssl_context' when using ssl
# if we are using python < 2.7.10, 'create_default_https_context' is never used
ssl._create_default_https_context = create_redhat_ssl_context


class SoapNull(MessagePlugin):
    """suds plugin that is called before any suds message is sent to the remote
    server. It adds the xsi:nil=true attribute to any element that is blank.
    Without this plugin, a number of functions that were supposed to accept
    null parameters did not work.
    """
    def marshalled(self, context):
        # Go through every node in the document and check if it is empty and
        # if so set the xsi:nil tag to true
        context.envelope.walk(self.add_nil)

    def add_nil(self, element):
        """Used as a filter function with walk to add xsi:nil to blank attrs.
        """
        if element.isempty() and not element.isnil():
            element.attributes.append(Attribute('xsi:nil', 'true'))


class Session(object):

    def _url_for_name(self, service_name):
        """generate the full URL for the WSDL client services"""
        return '{0}/ws/services/{1}WebService?wsdl'.format(self._server.url,
                                                           service_name)

    def __init__(self, server, caching_policy, timeout):
        """Session constructor, initialize the WSDL clients

           Args:
                server: server object that the session connects to
                caching_policy: determines the caching policy of the SUDS conn
                timeout: HTTP timeout for the connection
        """
        self._server = server
        self._last_request_at = None
        self._session_id_header = None
        self._session_client = _suds_client_wrapper(
            self._url_for_name('Session'), None, caching_policy, timeout)
        # In certain circumstances when using a load balancer, the wsdl will
        # switch nodes for an unknown reason. This fix gets the specific node
        # that was logged into and uses it for all future server interactions.
        # The cause of this problem is unknown as it works in most instances
        # without this fix. Another solutions that was tried was to add the
        # load balancer's sticky bit cookie to the headers, but that did not
        # have any effect.
        full_url = self._session_client._suds_client.wsdl.types[0]. \
            definitions["services"][0]["ports"][0]["location"]
        p_url = urlparse(full_url)
        o_url = urlparse(self._server.url)
        self._server.url = "%s://%s%s" % (
            p_url.scheme, p_url.hostname, o_url.path)
        self.builder_client = _suds_client_wrapper(
            self._url_for_name('Builder'), self, caching_policy, timeout)
        self.planning_client = _suds_client_wrapper(
            self._url_for_name('Planning'), self, caching_policy, timeout)
        self.project_client = _suds_client_wrapper(
            self._url_for_name('Project'), self, caching_policy, timeout)
        self.security_client = _suds_client_wrapper(
            self._url_for_name('Security'), self, caching_policy, timeout)
        self.test_management_client = _suds_client_wrapper(
            self._url_for_name('TestManagement'), self, caching_policy,
            timeout)
        self.tracker_client = _suds_client_wrapper(
            self._url_for_name('Tracker'), self, caching_policy, timeout)

    def _login(self):
        """login to the Polarion API"""
        sc = self._session_client
        sc.service.logIn(self._server.login, self._server.password)
        id_element = sc.last_received(). \
            childAtPath('Envelope/Header/sessionID')
        sessionID = id_element.text
        sessionNS = id_element.namespace()
        self._session_id_header = suds.sax.element.Element(
            'sessionID', ns=sessionNS).setText(sessionID)
        sc.set_options(soapheaders=self._session_id_header)
        self._last_request_at = time.time()

    def _logout(self):
        """logout from Polarion server"""
        self._session_client.service.endSession()

    def _reauth(self):
        """auto relogin after timeout, set in the getattr function of each
        client obj
        """
        sc = self._session_client
        duration = time.time() - self._last_request_at
        if duration > self._server.relogin_timeout and not \
                sc.service.hasSubject():
            logger.debug("Session expired, trying to log in again")
            self._login()
        else:
            self._last_request_at = time.time()

    def tx_begin(self):
        self._session_client.service.beginTransaction()

    def tx_commit(self):
        self._session_client.service.endTransaction(False)

    def tx_rollback(self):
        self._session_client.service.endTransaction(True)

    def tx_release(self):
        if self._session_client.service.transactionExists():
            self.tx_rollback()

    def tx_in(self):
        """Function checks if a transaction is in progress. You can not have a
        transaction within another transaction. This function helps the system
        determine if it should start a new transaction or if it is already in
        the middle of one.

        Returns:
            bool
        """
        return self._session_client.service.transactionExists()


class _suds_client_wrapper:
    """class that manages the WSDL clients"""

    def __init__(self, url, enclosing_session, caching_policy, timeout):
        """has the actual WSDL client as a private _suds_client attribute so
        that the "magic" __getattr__ function will be able to verify
        functions called on it and after processing to call the WSDL function

        Args:
            url (str): the URL of the Polarion server.
            enclosing_session: the HTTP session that the requests are sent
                               through
            caching_policy (int): is a configuration parameter that specifies
                                 either 0 or 1. When it is set correctly, the
                                 client always goes to the same host when using
                                 a load balancer. Unfortunately, some
                                 workstations require 1 and others 0 and I have
                                 not understood what the qualification is.
            timeout (int): The HTTP timeout of the connection
        """
        plugin = SoapNull()
        # adding cookies gotten from site in session__init__. This will
        # guarantee that all clients use the load balancer cookies and go to
        # the same node.
        self._suds_client = suds.client.Client(
            url,
            plugins=[plugin],
            cachingpolicy=caching_policy,
            timeout=timeout)
        self._enclosing_session = enclosing_session

    def __getattr__(self, attr):
        # every time a client function is called, this verifies that there is
        # still an active connection and if not, it reconnects.
        logger.debug("attr={0} self={1}".format(attr, self.__dict__))
        if attr == "service" and self._enclosing_session and \
                self._enclosing_session._session_id_header is not None:
            logger.debug("Calling hook before _suds_client_wrapper.service "
                         "access")
            self._enclosing_session._reauth()
            self._suds_client.set_options(
                soapheaders=self._enclosing_session._session_id_header)
        return getattr(self._suds_client, attr)

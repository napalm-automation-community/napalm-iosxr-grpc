# Copyright 2019 Mircea Ulinic. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
gRPC-based NAPALM driver for IOS-XR.
"""
from __future__ import unicode_literals

import logging

import napalm.base.helpers
from napalm.base import NetworkDriver
from napalm.base.utils import string_parsers, py23_compat
from napalm.base.exceptions import (
    ConnectAuthError,
    ConnectionException,
    CommandErrorException,
    SessionLockedException,
)

from iosxr_grpc.cisco_grpc_client import CiscoGRPCClient


class gRPCXRDriver(NetworkDriver):
    """
    gRPCXRDriver driver class.
    """
    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.optional_args = {}
        if optional_args:
            self.optional_args = optional_args
        self.port = self.optional_args.get("port", 57777)
        self.tls_key = self.optional_args.get("tls_key")
        self.tls_server_name = self.optional_args.get("tls_server_name")

    def open(self):
        """Establish connection with the network device."""
        log.debug("Establishing the connection over gRPC as %s@%s:%d", self.username, self.hostname, self.port)
        self.driver = CiscoGRPCClient(
            self.hostname,
            self.port,
            self.timeout,
            self.username,
            self.password
        )
        raise_err = None
        raise_class = ConnectionException
        err, result = self.driver.showcmdtextoutput("show clock")
        if err:
            err_obj = {}
            try:
                err_obj = ast.literal_eval(err)
            except (SyntaxError, ValueError) as parse_err:
                log.error('Unable to parse the error return from %s', err, exc_info=True)
            raise_class = None
            if 'cisco-grpc:errors' in err_obj and 'error' in err_obj['cisco-grpc:errors']:
                err_msg = err_obj['cisco-grpc:errors']['error'][0]
                if err_msg['error-tag'] == 'access-denied':
                    raise_class = ConnectAuthError
                raise_err = raise_class(err_msg['error-message'])
                raise_err.error_tag = err_msg['error-tag']
                raise_err.error_type = err_msg['error-type']
                raise_err.error_severity = err_msg['error-severity']
                log.error(err_msg['error-message'])
                raise(raise_err)

    def get_facts(self):
        """Collecting facts from the device."""


    def close(self):
       """Disconnect."""
       log.debug("Disconnecting from %s", self.hostname)
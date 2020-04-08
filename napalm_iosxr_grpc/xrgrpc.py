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

import json
import logging

from napalm.base import NetworkDriver
from napalm.base.exceptions import (
    NapalmException,
    ConnectAuthError,
    ConnectionException,
    CommandErrorException,
    CommandTimeoutException,
)

import grpc.framework.interfaces.face.face
from iosxr_grpc.cisco_grpc_client import CiscoGRPCClient

log = logging.getLogger(__name__)


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
        self.port = self.optional_args.get("port", 57400)
        self.tls_key = self.optional_args.get("tls_key")
        self.tls_server_name = self.optional_args.get("tls_server_name")

    def _execute(self, method, *args, **kwargs):
        fmt = kwargs.pop("format", "json")
        try:
            err, result = getattr(self.driver, method)(*args, **kwargs)
        except grpc.framework.interfaces.face.face.ExpirationError as timeout_err:
            raise CommandTimeoutException(timeout_err)
        if err:
            err_obj = {}
            try:
                err_obj = json.loads(err)
            except (json.decoder.JSONDecodeError, TypeError):
                log.error("Unable to parse the error from %s", err, exc_info=True)
            raise_class = None
            if (
                "cisco-grpc:errors" in err_obj
                and "error" in err_obj["cisco-grpc:errors"]
            ):
                err_msg = err_obj["cisco-grpc:errors"]["error"][0]
                if err_msg["error-tag"] == "access-denied":
                    raise_class = ConnectAuthError
                else:
                    raise_class = CommandErrorException
                raise_err = raise_class(err_msg["error-message"])
                raise_err.error_tag = err_msg["error-tag"]
                raise_err.error_type = err_msg["error-type"]
                raise_err.error_severity = err_msg["error-severity"]
                log.error(err_msg["error-message"])
                raise (raise_err)
        if fmt == "text":
            return result
        try:
            ret = json.loads(result)
        except (json.decoder.JSONDecodeError, TypeError):
            log.error("Unable to process the return %s", result, exc_info=True)
            raise
        return ret

    def open(self):
        """Establish connection with the network device."""
        log.debug(
            "Establishing the connection over gRPC as %s@%s:%d",
            self.username,
            self.hostname,
            self.port,
        )
        kwargs = {}
        if self.tls_key and self.tls_server_name:
            kwargs = {"creds": self.tls_key, "options": self.tls_server_name}
        self.driver = CiscoGRPCClient(
            self.hostname,
            self.port,
            self.timeout,
            self.username,
            self.password,
            **kwargs
        )
        log.debug('Executing "show clock" to check the connection')
        try:
            self._execute("showcmdtextoutput", "show clock", format="text")
        except NapalmException as err:
            raise ConnectionException(err)

    def get_facts(self):
        """Collecting facts from the device."""
        # Extracting the details from Rack 0 specifically. Unfortunately, the
        # way ``get_facts`` has been historically designed, it doesn't provide
        # support for stacked devices.
        path = '{"openconfig-platform:components": [{"component": {"name": "Rack 0"}}]}'
        res = self._execute("getoper", path)
        component = res["openconfig-platform:components"]["component"][0]["state"]

        # Here we'd be executing an RPC request for openconfig-system if it
        # wouldn't require bleeding edge IOS-XR 7+. FFS.
        hostname = (
            self._execute("showcmdtextoutput", "show running-config hostname")[1]
            .splitlines()[2]
            .split("hostname ")[1]
        )

        domain_name = (
            self._execute("showcmdtextoutput", "show running-config domain name")[1]
            .splitlines()[2]
            .split("domain name ")[1]
        )

        fqdn = "{hostname}.{domain_name}".format(
            hostname=hostname, domain_name=domain_name
        )

        # For the uptime, the only solution seems to be the output from
        # ``show version``, which is like:
        # System uptime is 9 weeks 4 days 20 hours 54 minutes
        # It's the last thing I wanna do parsing that.

        return {
            "vendor": "Cisco",
            "model": component["description"],
            "os_version": component["software-version"],
            "serial_number": component["serial-no"],
            "uptime": None,
            "hostname": hostname,
            "fqdn": fqdn,
        }

    def close(self):
        """Disconnect."""
        log.debug("Disconnecting from %s", self.hostname)

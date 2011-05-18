#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""End to end tests for ProtoRPC."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import logging
import unittest

from google.appengine.ext import webapp

from protorpc import protojson
from protorpc import remote
from protorpc import test_util
from protorpc import webapp_test_util

package = 'test_package'


class EndToEndTest(webapp_test_util.EndToEndTestBase):

  def testSimpleRequest(self):
    self.assertEquals(test_util.OptionalMessage(string_value='+blar'),
                      self.stub.optional_message(string_value='blar'))

  def testMissingContentType(self):
    code, content, headers = self.RawRequestError(
      'optional_message',
      content='{"string_value": "blar"}',
      content_type='')
    self.assertEquals(400, code)
    self.assertEquals('', content)
    self.assertEquals(headers['content-type'], 'text/html; charset=utf-8')

  def testUnsupportedContentType(self):
    code, content, headers = self.RawRequestError(
      'optional_message',
      content='{"string_value": "blar"}',
      content_type='image/png')
    self.assertEquals(415, code)
    self.assertEquals('', content)
    self.assertEquals(headers['content-type'], 'text/html; charset=utf-8')

  def testUnsupportedHttpMethod(self):
    code, content, headers = self.RawRequestError('optional_message',
                                                  content=None)
    self.assertEquals(405, code)
    self.assertEquals('', content)
    self.assertEquals(headers['content-type'], 'text/html; charset=utf-8')

  def testMethodNotFound(self):
    self.assertRaisesWithRegexpMatch(remote.MethodNotFoundError,
                                     'Unrecognized RPC method: does_not_exist',
                                     self.alternate_stub.does_not_exist)

  def testBadMessageError(self):
    code, content, headers = self.RawRequestError('nested_message',
                                                  content='{}')
    self.assertEquals(400, code)
    self.assertEquals(
      protojson.encode_message(remote.RpcStatus(
        state=remote.RpcState.REQUEST_ERROR,
        error_message=('Error parsing ProtoRPC request '
                       '(Unable to parse request content: '
                       'Message NestedMessage is missing '
                       'required field a_value)'))),
      content)
    self.assertEquals(headers['content-type'], 'application/json')

  def testApplicationError(self):
    try:
      self.stub.raise_application_error()
    except remote.ApplicationError, err:
      self.assertEquals('This is an application error', err.message)
      self.assertEquals('ERROR_NAME', err.error_name)
    else:
      self.fail('Expected application error')

  def testRpcError(self):
    try:
      self.stub.raise_rpc_error()
    except remote.ServerError, err:
      self.assertEquals('Internal Server Error', err.message)
    else:
      self.fail('Expected server error')

  def testUnexpectedError(self):
    try:
      self.stub.raise_unexpected_error()
    except remote.ServerError, err:
      self.assertEquals('Internal Server Error', err.message)
    else:
      self.fail('Expected server error')

  def testBadResponse(self):
    try:
      self.stub.return_bad_message()
    except remote.ServerError, err:
      self.assertEquals('Internal Server Error', err.message)
    else:
      self.fail('Expected server error')


def main():
  unittest.main()


if __name__ == '__main__':
  main()

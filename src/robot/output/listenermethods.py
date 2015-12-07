#  Copyright 2008-2015 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from robot.utils import get_error_details, py2to3

from .listenerarguments import ListenerArguments
from .logger import LOGGER


@py2to3
class ListenerMethods(object):

    def __init__(self, method_name, listeners):
        self._methods = []
        if listeners:
            self._register_methods(method_name, listeners)
        argument_handler = ListenerArguments.by_method_name(method_name)
        self._get_arguments = argument_handler.get_arguments

    def _register_methods(self, method_name, listeners):
        for listener in listeners:
            method = getattr(listener, method_name)
            if method:
                self._methods.append(ListenerMethod(method, listener.name))

    def __call__(self, *args):
        if self._methods:
            args = self._get_arguments(*args)
            for method in self._methods:
                method(args)

    def __nonzero__(self):
        return bool(self._methods)


class LibraryListenerMethods(object):

    def __init__(self, method_name):
        self._method_stack = []
        self._method_name = method_name
        argument_handler = ListenerArguments.by_method_name(method_name)
        self._get_arguments = argument_handler.get_arguments

    def new_suite_scope(self):
        self._method_stack.append([])

    def discard_suite_scope(self):
        self._method_stack.pop()

    def register(self, listeners, library):
        methods = self._method_stack[-1]
        for listener in listeners:
            method = getattr(listener, self._method_name)
            if method:
                info = ListenerMethod(method, listener.name, library)
                methods.append(info)

    def unregister(self, library):
        methods = [m for m in self._method_stack[-1] if m.library is not library]
        self._method_stack[-1] = methods

    def __call__(self, *args, **conf):
        methods = self._get_methods(**conf)
        if methods:
            args = self._get_arguments(*args)
            for method in methods:
                method(args)

    def _get_methods(self, library=None):
        if not (self._method_stack and self._method_stack[-1]):
            return []
        methods = self._method_stack[-1]
        if library:
            return [m for m in methods if m.library is library]
        return methods


class ListenerMethod(object):
    # Flag to avoid recursive listener calls.
    called = False

    def __init__(self, method, listener_name, library=None):
        self.method = method
        self.listener_name = listener_name
        self.library = library

    def __call__(self, args):
        if self.called:
            return
        try:
            ListenerMethod.called = True
            self.method(*args)
        except:
            message, details = get_error_details()
            LOGGER.error("Calling method '%s' of listener '%s' failed: %s"
                         % (self.method.__name__, self.listener_name, message))
            LOGGER.info("Details:\n%s" % details)
        finally:
            ListenerMethod.called = False
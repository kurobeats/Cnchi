#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# controller.py
#
# Copyright © 2013-2016 Antergos
#
# This file is part of Cnchi.
#
# Cnchi is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Cnchi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# The following additional terms are in effect as per Section 7 of the license:
#
# The preservation of all legal notices and author attributions in
# the material or in the Appropriate Legal Notices displayed
# by works containing it is required.
#
# You should have received a copy of the GNU General Public License
# along with Cnchi; If not, see <http://www.gnu.org/licenses/>.

""" HTML/JavaScript UI Controller """

# Standard Lib
import time

from _base_object import (
    ascii_uppercase,
    choice,
    json,
    sys
)

# 3rd Party Libs
from _base_object import GLib

# This application
from _base_object import (
    BaseObject,
    Singleton
)
from .container import MainContainer
from .main_window import MainWindow
from .pages import PagesHelper


class ReactController(BaseObject, metaclass=Singleton):
    """
    React Controller

    Class Attributes:
        _emit_js_tpl (str): Javascript string used to emit signals in web_view.
        See also `BaseObject.__doc__`

    """

    _emit_js_tpl = 'window.{0} = {1}; window.cnchi.js_bridge_handler("{0}");'

    def __init__(self, name='react_controller', *args, **kwargs):

        super().__init__(name=name, *args, **kwargs)

        self.current_page = None

        main_window = MainWindow()
        main_container = MainContainer()

        main_window.widget.add(self._web_view)
        self._initialize_pages()

    @staticmethod
    def _generate_js_temp_variable_name():
        var = ''.join(choice(ascii_uppercase) for i in range(6))
        return '__{}'.format(var)

    def _initialize_pages(self):
        self._pages_helper = PagesHelper()
        self.pages = self._pages_helper.page_names

    def emit_js(self, cmd, *args):
        """
        Pass data to a JavaScript handler in the web_view.

        Args:
            cmd (str): The name of the JavaScript function to call.
            *args (str): Arguments to pass to the function (optional).

        """

        # if cmd not in self._allowed_signals:
        #     self.logger.error('Signal: %s is not allowed!', cmd)
        #     return

        cmd = cmd.replace('-', '_')
        msg = json.dumps(dict(cmd=cmd, args=list(args)))
        var = self._generate_js_temp_variable_name()
        msg = self._emit_js_tpl.format(var, msg)

        self._web_view.run_javascript(msg, None, None, None)

    def js_log_message_cb(self, level, msg, *args):
        # TODO: Modify logging formatter so that it doesnt include this method's name/location.
        level = level if level else 'debug'

        _logger = getattr(self.logger, level)

        _logger(msg, *args)

    def set_current_page(self, identifier):
        page = self._pages_helper.get_page(identifier)

        if page is None:
            raise ValueError('page cannot be None!')

        page_uri = 'cnchi://{0}.page'.format(page.name)

        page.prepare()
        self._web_view.load_uri(page_uri)

    def trigger_js_event(self, event_name, *args):
        """
        Trigger a JavaScript event and optionally pass data to handler in the web_view.

        Args:
            event_name (str): The name of the JavaScript event to trigger.
            *args (str): Arguments to pass to the event handlers (optional).

        """

        GLib.idle_add(self._main_window.emit, event_name, *args)
        GLib.idle_add(self.emit_js, 'trigger-event', event_name, *args)


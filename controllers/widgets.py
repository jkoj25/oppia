# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main package for the widget repository."""

__author__ = 'sll@google.com (Sean Lip)'

import json

from controllers.base import BaseHandler
from models.widget import InteractiveWidget
from models.widget import NonInteractiveWidget
import utils

from google.appengine.api import users


class WidgetRepositoryPage(BaseHandler):
    """Displays the widget repository page."""

    def get(self):
        """Returns the widget repository page."""
        self.values.update({
            'js': utils.get_js_controllers(['widgetRepository']),
        })
        if self.request.get('iframed') == 'true':
            self.values['iframed'] = True
        if self.request.get('interactive') == 'true':
            self.values['interactive'] = True
        if users.is_current_user_admin():
            self.values['admin'] = True
        self.render_template('widgets/widget_repository.html')


class WidgetRepositoryHandler(BaseHandler):
    """Provides data to populate the widget repository page."""

    def get_widgets(self, widget_class):
        """Load widgets from the datastore."""
        response = {}

        for widget in widget_class.query():
            category = widget.category
            if category not in response:
                response[category] = []
            response[category].append(
                widget_class.get_with_params(widget.id, {})
            )

        for category in response:
            response[category].sort()
        return response

    def get(self):  # pylint: disable-msg=C6409
        """Handles GET requests."""
        if self.request.get('interactive') == 'true':
            response = self.get_widgets(InteractiveWidget)
        else:
            response = self.get_widgets(NonInteractiveWidget)

        self.response.write(json.dumps({'widgets': response}))


class InteractiveWidgetHandler(BaseHandler):
    """Handles requests relating to interactive widgets."""

    def get(self, widget_id):
        """Handles GET requests."""
        response = InteractiveWidget.get_with_params(widget_id)
        self.response.write(json.dumps({'widget': response}))

    def post(self, widget_id):
        """Handles POST requests, for parameterized widgets."""
        payload = json.loads(self.request.get('payload'))

        params = payload.get('params', {})
        if isinstance(params, list):
            new_params = {}
            for item in params:
                new_params[item['name']] = item['default_value']
            params = new_params

        state_params_dict = {}
        state_params_given = payload.get('state_params')
        if state_params_given:
            for (key, values) in state_params_given.iteritems():
                # Pick a random parameter for each key.
                state_params_dict[key] = utils.get_random_choice(values)

        response = InteractiveWidget.get_with_params(
            widget_id, params=utils.parse_dict_with_params(
                params, state_params_dict)
        )

        self.response.write(json.dumps({'widget': response}))

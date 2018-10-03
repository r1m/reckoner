# -- coding: utf-8 --

# Copyright 2017 Reactive Ops Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys
import logging
import subprocess


class Config(object):
    _config = {}

    def __init__(self):
        self.__dict__ = self._config
        self._installed_repositories = []

    @property
    def home(self):

        if self._config.get("home") is None:
            helm_home = os.environ.get('HELM_HOME')
            fallback_home = os.environ.get('HOME') + "/.helm"
            if helm_home is not None:
                self._config['home'] = helm_home
            else:
                self._config['home'] = fallback_home
                logging.warn("$HELM_HOME not set. Using ~/.helm")

        return self._config['home']

    @property
    def archive(self):
        if 'archive' not in self._config:
            archive = self.home + '/cache/archive'
            if not os.path.isdir(archive):
                logging.warn("{} does not exist. Have you run `helm init`?".format(archive))
            self._config['archive'] = archive

        return self._config['archive']

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        logging.debug("Config: {} is {}".format(name, value))

    def __str__(self):
        return str(self._config)

    def __iter__(self):
        return iter(self._config)

    @property
    def installed_repositories(self):
        if self._installed_repositories != []:
            return self._installed_repositories

        args = ['helm', 'repo', 'list']
        for repo in [line.split() for line in subprocess.check_output(args).split('\n')[1:-1]]:
            _repo = {'name': repo[0], 'url': repo[1]}
            if _repo not in self._installed_repositories:
                self._installed_repositories.append(_repo)
        logging.debug("Getting installed repositories: {}".format(self._installed_repositories))
        return self._installed_repositories

    @property
    def current_context(self):
        """ Returns the current cluster context """
        args = ['kubectl', 'config', 'current-context']
        resp = subprocess.check_output(args)
        return resp.strip()

    @property
    def helm_version(self):
        """ return version of installed helm binary """
        if self.local_development:
            return True
        args = ['helm', 'version', '--client']
        resp = subprocess.check_output(args)
        return resp.replace('Client: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')

    @property
    def tiller_present(self):
        """
        Detects if tiller is present in the currently configured cluster
        Accepts no arguments
        """

        logging.debug("Checking for Tiller")
        if self.local_development:
            return True

        try:
            FNULL = open(os.devnull, 'w')
            subprocess.check_call(['helm', 'list'], stdout=FNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return False
        return True
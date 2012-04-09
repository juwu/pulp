# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
import logging

from pulp.server.db.model.gc_repository import Repo

_log = logging.getLogger('pulp')

version = 40

def migrate():
    _log.info('migration to data model version %d started' % version)

    collection = Repo.get_collection()
    for repo in collection.find({}):
        if 'content_unit_count' in repo:
            repo.pop('content_unit_count', None)
            collection.save(repo, safe=True)

    _log.info('migration to data model version %d complete' % version)
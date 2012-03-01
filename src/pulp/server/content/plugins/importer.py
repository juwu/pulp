# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


class Importer(object):
    """
    Base class for Pulp content importers. Importers must subclass this class
    in order for Pulp to identify it as a valid importer during discovery.
    """

    # -- plugin lifecycle -----------------------------------------------------

    @classmethod
    def metadata(cls):
        """
        Used by Pulp to classify the capabilities of this importer. The
        following keys must be present in the returned dictionary:

        * id - Programmatic way to refer to this importer. Must be unique
               across all importers. Only letters and underscores are valid.
        * display_name - User-friendly identification of the importer.
        * types - List of all content type IDs that may be imported using this
               importer.

        This method call may be made multiple times during the course of a
        running Pulp server and thus should not be used for initialization
        purposes.

        @return: description of the importer's capabilities
        @rtype:  dict
        """
        raise NotImplementedError()

    # -- repo lifecycle -------------------------------------------------------

    def validate_config(self, repo, config):
        """
        Allows the importer to check the contents of a potential configuration
        for the given repository. This call is made both for the addition of
        this importer to a new repository as well as updating the configuration
        for this importer on a previously configured repository. The implementation
        should use the given repository data to ensure that updating the
        configuration does not put the repository into an inconsistent state.

        @param repo: metadata describing the repository to which the
                     configuration applies
        @type  repo: L{pulp.server.content.plugins.data.Repository}

        @param config: plugin configuration instance; the proposed repo
                       configuration is found within
        @type  config: L{pulp.server.content.plugins.config.PluginCallConfiguration}

        @return: True if the configuration is valid; False otherwise
        @rtype:  bool
        """
        raise NotImplementedError()

    def importer_added(self, repo, config):
        """
        Called upon the successful addition of an importer of this type to
        a repository. This hook allows the importer to do any initial setup
        it needs to prior to the first sync.

        This call should raise an exception in the case where the importer
        is unable to successfully set up anything it will need to perform any
        repository actions against the given repository. In this case, Pulp
        will mark the importer as broken and repository operations that rely
        on the importer will be unavailable for the given repository.

        @param repo: metadata describing the repository
        @type  repo: L{pulp.server.content.plugins.model.Repository}

        @param config: plugin configuration
        @type  config: L{pulp.server.content.plugins.config.PluginCallConfiguration}
        """
        pass

    def importer_removed(self, repo, config):
        """
        Called when an importer of this type is removed from a repository.
        This hook allows the importer to clean up any temporary files that may
        have been created during the repository creation or sync process.

        This call does not need to delete any content that has been
        synchronized by this importer. Imported content units are deleted through
        a separate process in Pulp.

        The importer may use the contents of the working directory in cleanup.
        It is not required that the contents of this directory be deleted by
        the importer; Pulp will ensure it is wiped following this call.

        If this call raises an exception, the importer will still be removed
        from the repository and the working directory contents will still
        be wiped by Pulp.

        @param repo: metadata describing the repository
        @type  repo: L{pulp.server.content.plugins.model.Repository}

        @param config: plugin configuration
        @type  config: L{pulp.server.content.plugins.config.PluginCallConfiguration}
        """
        pass

    def import_units(self, repo, units, import_conduit, config):
        """
        Import content units into the given repository. This method will be
        called in a number of different situations:
         * A user is attempting to migrate a content unit from one repository
           into the repository that uses this importer
         * A user has uploaded a content unit to the Pulp server and is
           attempting to associate it to a repository that uses this importer
         * An existing repository is being cloned into a repository that
           uses this importer

        In all cases, the expected behavior is that the importer uses this call
        as an opportunity to perform any changes it needs to its working
        files for the repository to incorporate the new units.

        The units may or may not exist in Pulp prior to this call. The call to
        add a unit to Pulp is idempotent and should be made anyway to ensure
        the case where a new unit is being uploaded to Pulp is handled.

        @param repo: metadata describing the repository
        @type  repo: L{pulp.server.content.plugins.data.Repository}

        @param units: list of objects describing the units to import in
                      this call
        @type  units: list of L{pulp.server.content.plugins.data.Unit}

        @param import_conduit: provides access to relevant Pulp functionality
        @type  import_conduit: ?

        @param config: plugin configuration
        @type  config: L{pulp.server.content.plugins.config.PluginCallConfiguration}
        """
        raise NotImplementedError()

    def remove_units(self, repo, units, remove_conduit):
        """
        Removes content units from the given repository.

        This method is intended to provide the importer with a chance to remove
        the units from the importer's working directory for the repository.

        This call will not result in the unit being deleted from Pulp itself.
        The importer should, however, use the conduit to tell Pulp to remove
        the association between the unit and the given repository.

        @param repo: metadata describing the repository
        @type  repo: L{pulp.server.content.plugins.data.Repository}

        @param units: list of objects describing the units to import in
                      this call
        @type  units: list of L{pulp.server.content.plugins.data.Unit}

        @param remove_conduit: provides access to relevant Pulp functionality
        @type  remove_conduit: ?
        """
        raise NotImplementedError()

    # -- actions --------------------------------------------------------------

    def sync_repo(self, repo, sync_conduit, config):
        """
        Synchronizes content into the given repository. This call is responsible
        for adding new content units to Pulp as well as associating them to the
        given repository.

        While this call may be implemented using multiple threads, its execution
        from the Pulp server's standpoint should be synchronous. This call should
        not return until the sync is complete.

        It is not expected that this call be atomic. Should an error occur, it
        is not the responsibility of the importer to rollback any unit additions
        or associations that have been made.

        The returned report object is used to communicate the results of the
        sync back to the user. Care should be taken to i18n the free text "log"
        attribute in the report if applicable.

        @param repo: metadata describing the repository
        @type  repo: L{pulp.server.content.plugins.data.Repository}

        @param sync_conduit: provides access to relevant Pulp functionality
        @type  sync_conduit: L{pulp.server.content.conduits.repo_sync.RepoSyncConduit}

        @param config: plugin configuration
        @type  config: L{pulp.server.content.plugins.config.PluginCallConfiguration}

        @return: report of the details of the sync
        @rtype:  L{pulp.server.content.plugins.model.SyncReport}
        """
        raise NotImplementedError()
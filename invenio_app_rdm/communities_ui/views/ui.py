# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Communities UI blueprints module."""

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user
from flask_menu import current_menu
from invenio_communities.communities.resources.serializer import (
    UICommunityJSONSerializer,
)
from invenio_communities.errors import CommunityDeletedError
from invenio_i18n import lazy_gettext as _
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError
from invenio_records_resources.services.errors import PermissionDeniedError

from ..searchapp import search_app_context
from .communities import (
    communities_detail,
    organizations_detail,
    organizations_home,
    persons_detail,
    communities_home,
    persons_home
)


#
# Error handlers
#
def not_found_error(error):
    """Handler for 'Not Found' errors."""
    return render_template(current_app.config["THEME_404_TEMPLATE"]), 404


def record_tombstone_error(error):
    """Tombstone page."""
    # the RecordDeletedError will have the following properties,
    # while the PIDDeletedError won't
    record = getattr(error, "record", None)
    if (record_ui := getattr(error, "result_item", None)) is not None:
        if record is None:
            record = record_ui._record
        record_ui = UICommunityJSONSerializer().dump_obj(record_ui.to_dict())

    # render a 404 page if the tombstone isn't visible
    if not record.tombstone.is_visible:
        return not_found_error(error)

    # we only render a tombstone page if there is a record with a visible tombstone
    return (
        render_template(
            "invenio_communities/tombstone.html",
            record=record_ui,
        ),
        410,
    )


def _is_branded_community():
    """Function used to check if community is branded."""
    community = request.community
    if community.get("theme", {}).get("enabled", False):
        return True
    return False


def record_permission_denied_error(error):
    """Handle permission denier error on record views."""
    if not current_user.is_authenticated:
        # trigger the flask-login unauthorized handler
        return current_app.login_manager.unauthorized()
    return render_template(current_app.config["THEME_403_TEMPLATE"]), 403


def create_ui_blueprint(app):
    """Register blueprint routes on app."""
    routes = app.config["RDM_COMMUNITIES_ROUTES"]

    blueprint = Blueprint(
        "invenio_app_rdm_communities",
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    blueprint.add_url_rule(
        routes["community-detail"],
        view_func=communities_detail,
        strict_slashes=False,
    )

    blueprint.add_url_rule(
        routes["person-detail"],
        view_func=persons_detail,
        strict_slashes=False,
    )

    blueprint.add_url_rule(
        routes["organization-detail"],
        view_func=organizations_detail,
        strict_slashes=False,
    )

    blueprint.add_url_rule(
        routes["community-home"],
        view_func=communities_home,
    )

    blueprint.add_url_rule(
        routes["person-home"],
        view_func=persons_home,
    )

    blueprint.add_url_rule(
        routes["organization-home"],
        view_func=organizations_home,
    )

    @blueprint.before_app_first_request
    def register_menus():
        """Register community menu items."""
        show_specific_communities = current_app.config.get("COMMUNITIES_SHOW_SPECIFIC_TYPES", False)
        communities = current_menu.submenu("communities")
        communities.submenu("home").register(
            "invenio_app_rdm_communities.communities_home",
            text=_("Home"),
            order=1,
            visible_when=_is_branded_community,
            expected_args=["pid_value"],
            **dict(icon="home", permissions="can_read"),
        )
        communities.submenu("search").register(
            "invenio_app_rdm_communities.communities_detail",
            text=_("Records"),
            order=2,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )

        if show_specific_communities:
            persons = current_menu.submenu("persons")
            persons.submenu("home").register(
                "invenio_app_rdm_communities.persons_home",
                text=_("Home"),
                order=1,
                visible_when=_is_branded_community,
                expected_args=["pid_value"],
                **dict(icon="home", permissions="can_read"),
            )

            persons.submenu("search").register(
                "invenio_app_rdm_communities.persons_detail",
                text=_("Records"),
                order=2,
                expected_args=["pid_value"],
                **dict(icon="search", permissions=True),
            )

            organizations = current_menu.submenu("organizations")
            organizations.submenu("home").register(
                "invenio_app_rdm_communities.organizations_home",
                text=_("Home"),
                order=1,
                visible_when=_is_branded_community,
                expected_args=["pid_value"],
                **dict(icon="home", permissions="can_read"),
            )

            organizations.submenu("search").register(
                "invenio_app_rdm_communities.organizations_detail",
                text=_("Records"),
                order=2,
                expected_args=["pid_value"],
                **dict(icon="search", permissions=True),
            )


    # Register error handlers
    blueprint.register_error_handler(
        PermissionDeniedError, record_permission_denied_error
    )
    blueprint.register_error_handler(PIDDeletedError, record_tombstone_error)
    blueprint.register_error_handler(CommunityDeletedError, record_tombstone_error)
    blueprint.register_error_handler(PIDDoesNotExistError, not_found_error)
    blueprint.register_error_handler(PIDDoesNotExistError, not_found_error)

    # Register context processor
    blueprint.app_context_processor(search_app_context)

    return blueprint

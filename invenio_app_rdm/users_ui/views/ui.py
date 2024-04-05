# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2021 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Communities UI views."""

from flask import Blueprint, current_app, render_template
from flask_login import current_user
from flask_menu import current_menu
from invenio_i18n import lazy_gettext as _

from ..searchapp import search_app_context
from .dashboard import (
    communities,
    organizations,
    requests,
    uploads,
    persons
)


#
# Error handlers
#
def not_found_error(error):
    """Handler for 'Not Found' errors."""
    return render_template(current_app.config["THEME_404_TEMPLATE"]), 404


def record_permission_denied_error(error):
    """Handle permission denier error on record views."""
    if not current_user.is_authenticated:
        # trigger the flask-login unauthorized handler
        return current_app.login_manager.unauthorized()
    return render_template(current_app.config["THEME_403_TEMPLATE"]), 403


#
# Registration
#
def create_ui_blueprint(app):
    """Register blueprint routes on app."""
    routes = app.config.get("APP_RDM_USER_DASHBOARD_ROUTES")

    blueprint = Blueprint(
        "invenio_app_rdm_users",
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    blueprint.add_url_rule(
        routes["uploads"],
        view_func=uploads,
    )

    # Settings tab routes
    blueprint.add_url_rule(
        routes["communities"],
        view_func=communities,
    )

    blueprint.add_url_rule(
        routes["persons"],
        view_func=persons,
    )

    blueprint.add_url_rule(
        routes["organizations"],
        view_func=organizations,
    )

    blueprint.add_url_rule(
        routes["requests"],
        view_func=requests,
    )

    @blueprint.before_app_first_request
    def register_menus():
        """Register community menu items."""
        user_dashboard = current_menu.submenu("dashboard")
        user_dashboard.submenu("uploads").register(
            "invenio_app_rdm_users.uploads",
            text=_("My uploads"),
            order=1,
        )
        user_dashboard.submenu("communities").register(
            "invenio_app_rdm_users.communities",
            text=_("My communities"),
            order=2,
        )
        show_specific_communities = current_app.config.get("COMMUNITIES_SHOW_SPECIFIC_TYPES", False)
        if show_specific_communities:
            user_dashboard.submenu("organizations").register(
                "invenio_app_rdm_users.organizations",
                text=_("My organizations"),
                order=3,
            )
            user_dashboard.submenu("persons").register(
                "invenio_app_rdm_users.persons",
                text=_("My persons"),
                order=4,
            )
        user_dashboard.submenu("requests").register(
            "invenio_app_rdm_users.requests",
            text=_("My requests"),
            order=(5 if show_specific_communities else 3),
        )

    # Register context processor
    blueprint.app_context_processor(search_app_context)

    return blueprint

# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2024 Graz University of Technology.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Research Data Management."""

from flask import request, current_app
from flask_menu import current_menu
from invenio_i18n import lazy_gettext as _


def _is_branded_community():
    """Function used to check if community is branded."""
    community = request.community
    if community.get("theme", {}).get("enabled", False):
        return True
    return False


def finalize_app(app):
    """Finalize app."""
    init_menu(app)


def init_menu(app):
    """Init menu."""
    current_menu.submenu("actions.deposit").register(
        endpoint="invenio_app_rdm_users.uploads",
        text=_("My dashboard"),
        order=1,
    )

    current_menu.submenu("plus.deposit").register(
        endpoint="invenio_app_rdm_records.deposit_create",
        text=_("New upload"),
        order=1,
    )

    current_menu.submenu("notifications.requests").register(
        "invenio_app_rdm_users.requests",
        order=1,
    )

    user_dashboard = current_menu.submenu("dashboard")
    user_dashboard.submenu("uploads").register(
        endpoint="invenio_app_rdm_users.uploads",
        text=_("Uploads"),
        order=1,
    )
    user_dashboard.submenu("communities").register(
        endpoint="invenio_app_rdm_users.communities",
        text=_("Communities"),
        order=2,
    )
    show_specific_communities = current_app.config.get("COMMUNITIES_SHOW_SPECIFIC_TYPES", False)
    if show_specific_communities:
        user_dashboard.submenu("organizations").register(
            "invenio_app_rdm_users.organizations",
            text=_("Organizations"),
            order=3,
        )
        user_dashboard.submenu("persons").register(
            "invenio_app_rdm_users.persons",
            text=_("Persons"),
            order=4,
        )
    user_dashboard.submenu("requests").register(
        endpoint="invenio_app_rdm_users.requests",
        text=_("Requests"),
        order=(5 if show_specific_communities else 3),
    )

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
        order=2 if _is_branded_community else 1,
        expected_args=["pid_value"],
        **dict(icon="search", permissions=True),
    )
    communities.submenu("submit").register(
        "invenio_app_rdm_communities.community_static_page",
        text=_("Submit"),
        order=3,
        visible_when=_is_branded_community,
        endpoint_arguments_constructor=lambda: {
            "pid_value": request.view_args["pid_value"],
            "page_slug": "how-to-submit",
        },
        **dict(icon="upload", permissions="can_read"),
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
            order=2 if _is_branded_community else 1,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )
        persons.submenu("submit").register(
            "invenio_app_rdm_communities.community_static_page",
            text=_("Submit"),
            order=3,
            visible_when=_is_branded_community,
            endpoint_arguments_constructor=lambda: {
                "pid_value": request.view_args["pid_value"],
                "page_slug": "how-to-submit",
            },
            **dict(icon="upload", permissions="can_read"),
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
            order=2 if _is_branded_community else 1,
            expected_args=["pid_value"],
            **dict(icon="search", permissions=True),
        )
        organizations.submenu("submit").register(
            "invenio_app_rdm_communities.community_static_page",
            text=_("Submit"),
            order=3,
            visible_when=_is_branded_community,
            endpoint_arguments_constructor=lambda: {
                "pid_value": request.view_args["pid_value"],
                "page_slug": "how-to-submit",
            },
            **dict(icon="upload", permissions="can_read"),
        )


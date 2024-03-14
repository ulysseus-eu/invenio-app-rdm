# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Request views module."""

from flask import g, redirect, request, url_for
from invenio_communities.views.communities import render_community_theme_template
from invenio_communities.views.decorators import pass_community
from invenio_communities.utils import CommunityType
from invenio_rdm_records.proxies import current_community_records_service
from invenio_rdm_records.resources.serializers import UIJSONSerializer
from invenio_records_resources.services.errors import PermissionDeniedError


@pass_community(serialize=True)
def communities_detail(pid_value, community, community_ui):
    """Community detail page."""
    permissions = community.has_permissions_to(
        ["update", "read", "search_requests", "search_invites", "moderate"]
    )
    community_type = CommunityType(community.data["metadata"].get("type", {"id": "community"})["id"])
    endpoint = f"/api/{community_type.get_plural()}/{community.to_dict()['id']}/records"

    return render_community_theme_template(
        "invenio_communities/records/index.html",
        theme=community_ui.get("theme", {}),
        community=community,
        community_ui=community_ui,
        # Pass permissions so we can disable partially UI components
        # e.g Settings tab
        permissions=permissions,
        active_community_header_menu_item="search",
        endpoint=endpoint,
    )


@pass_community(serialize=True)
def persons_detail(pid_value, community, community_ui):
    """Person detail page."""
    return communities_detail(pid_value=pid_value, community=community, community_ui=community_ui)


@pass_community(serialize=True)
def organizations_detail(pid_value, community, community_ui):
    """Organization detail page."""
    return communities_detail(pid_value=pid_value, community=community, community_ui=community_ui)


@pass_community(serialize=True)
def communities_home(pid_value, community, community_ui):
    """Community home page."""
    _id = community.id
    query_params = request.args

    permissions = community.has_permissions_to(
        [
            "update",
            "read",
            "search_requests",
            "search_invites",
            "moderate",
        ]
    )
    if not permissions["can_read"]:
        raise PermissionDeniedError()

    theme_enabled = community._record.theme and community._record.theme.get(
        "enabled", False
    )

    if query_params or not theme_enabled:
        if community.data["metadata"].get("type") and community.data["metadata"]["type"]["id"] == "person":
            url = url_for(
                "invenio_app_rdm_communities.persons_detail",
                pid_value=community._record.slug,
                **request.args
            )
        elif community.data["metadata"].get("type") and community.data["metadata"]["type"]["id"] == "organization":
            url = url_for(
                "invenio_app_rdm_communities.organizations_detail",
                pid_value=community._record.slug,
                **request.args
            )
        else:
            url = url_for(
                "invenio_app_rdm_communities.communities_detail",
                pid_value=community._record.slug,
                **request.args
            )
        return redirect(url)
    else:
        recent_uploads = current_community_records_service.search(
            community_id=pid_value,
            identity=g.identity,
            params={
                "sort": "newest",
                "size": 3,
            },
            expand=True,
        )

        records_ui = UIJSONSerializer().dump_list(recent_uploads.to_dict())["hits"][
            "hits"
        ]

        return render_community_theme_template(
            "invenio_communities/details/home/index.html",
            theme=community_ui.get("theme", {}),
            community=community_ui,
            permissions=permissions,
            records=records_ui,
        )


@pass_community(serialize=True)
def persons_home(pid_value, community, community_ui):
    """Person home page."""
    return communities_home(pid_value=pid_value, community=community, community_ui=community_ui)


@pass_community(serialize=True)
def organizations_home(pid_value, community, community_ui):
    """Organization home page."""
    return communities_home(pid_value=pid_value, community=community, community_ui=community_ui)


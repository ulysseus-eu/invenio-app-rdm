# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2024 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-App-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Record migration script from InvenioRDM 11.0 to 12.0.

Disclaimer: This script is intended to be executed *only once*, namely when
upgrading from InvenioRDM 11.0 to 12.0!
If this script is executed at any other time, probably the best case scenario
is that nothing happens!


This script has been tested with following data:

- user
  - demo records of v11
  - demo communities of v11
  - cli created user of v11
  - ui created community (com_a)
  - ui created community private (com_b)
  - ui created record (rec_a.v1)
  - ui created v2 of record (rec_a.v1)
  - ui created record (rec_b.v1) added to community (com_a)
  - ui created draft (dra_a)
  - ui created draft (dra_b) added to community (com_b)
  - repository with records without managed doi
  - repository with records with managed doi
  - repository with records with managed doi without parent doi after migration
  - base vocabularies (no customized) usable after migration
  - record (rec_a.v1, rec_a.v2) findable after migration and rebuild of index

- administration
  - user panel list of users visible
  - drafts visible
  - records visible
"""
import argparse
import click
import os
import re
import sys

from click import secho
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.records.systemfields.access import ReviewPolicyEnum
from invenio_db import db
from invenio_rdm_records.fixtures import PrioritizedVocabulariesFixtures
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records.api import RDMDraft, RDMRecord
from invenio_records.api import Record
from invenio_rdm_records.records.models import RDMRecordMetadata


def migrate_review_policy(community_record):
    if community_record.is_deleted:
        return

    community_record["access"].setdefault(
        "review_policy", ReviewPolicyEnum.CLOSED.value
    )

def update_parent(record):
    """Update parent schema and parent communities for older records."""
    new_parent_schema = "local://records/parent-v3.0.0.json"
    record.parent["$schema"] = new_parent_schema

    if (
       isinstance(record.parent["access"]["owned_by"], list)
       and len(record.parent["access"]["owned_by"]) > 0
    ):
        record.parent.access.owned_by = {
            "user": record.parent["access"]["owned_by"][0]["user"]
        }

    if "pids" not in record.parent:
        record.parent["pids"] = {}

        if (
            current_app.config["DATACITE_ENABLED"]
            and "doi" in current_app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"]
            and current_app.config["RDM_PARENT_PERSISTENT_IDENTIFIERS"]["doi"][
                "is_enabled"
            ]
        ):
            pids = current_rdm_records.records_service.pids.parent_pid_manager.create_all(
                record.parent, pids={}, schemes={"doi"}
            )
            current_rdm_records.records_service.pids.parent_pid_manager.reserve_all(
                record.parent, pids
            )
            record.parent["pids"] = pids
            # Have to commit here otherwise register_or_update won't get
            # the above data
            record.parent.commit()

            if isinstance(record, RDMRecord):
                current_rdm_records.records_service.pids.register_or_update(
                    id_=record["id"],
                    identity=system_identity,
                    scheme="doi",
                    parent=True,
                )
    # Catch all commit for the parent
    record.parent.commit()

def update_record(record):
    # skipping deleted records because can't be committed
    if record.is_deleted:
        return

    try:
        secho(f"Updating record : {record.pid.pid_value}", fg="yellow")

        # otherwise the save would not work, due to new attributes
        # (media_files, parent_doi) used
        record["$schema"] = "local://records/record-v6.0.0.json"

        # Initialize media files as disabled if not any
        record.setdefault("media_files", {"enabled": False})
        if record.media_files.bucket is None:
            record.media_files.create_bucket()

        update_parent(record)

        record.commit()

        secho(f"> Updated parent: {record.parent.pid.pid_value}", fg="green")
        secho(f"> Updated record: {record.pid.pid_value}\n", fg="green")
        return None
    except Exception as e:
        secho(f"> Error {repr(e)}", fg="red")
        error = f"Record {record.pid.pid_value} failed to update"
        return error

def execute_upgrade():
    """Execute the upgrade from InvenioRDM 11.0 to 12.0.0.

    Please read the disclaimer on this module before thinking about executing
    this function!
    """
    secho("Starting data migration...", fg="green")

    # upgrading vocabularies
    pvf = PrioritizedVocabulariesFixtures(system_identity)
    pvf.load()

    # Migrating communities
    communities = Community.model_cls.query.all()

    for community_data in communities:
        community = Community(community_data.data, model=community_data)

        # production data could have problems without it
        if community:
            migrate_review_policy(community)
            community.commit()

    # Migrating records and drafts
    errors = []
    for page in range(RDMRecord.model_cls.query.count()//100):
        page_error = []
        for record_metadata in RDMRecord.model_cls.query.offset(100*page).limit(100):
            record = RDMRecord(record_metadata.data, model=record_metadata)
            error = update_record(record)

            if error:
                page_error.append(record.id)
                errors.append(error)
        if len(page_error) > 0:
            db.session.rollback()
            for record_metadata in RDMRecord.model_cls.query.offset(100*page).limit(100).filter_by(id.not_in(page_error)):
                record = RDMRecord(record_metadata.data, model=record_metadata)
                update_record(record)
        db.session.commit()

    for page in range(RDMDraft.model_cls.query.count()//100):
        page_error = []
        for draft_metadata in RDMDraft.model_cls.query.offset(100*page).limit(100):
            draft = RDMDraft(draft_metadata.data, model=draft_metadata)
            error = update_record(draft)
            if error:
                page_error.append(draft.id)
                errors.append(error)
        if len(page_error) > 0:
            db.session.rollback()
            for draft_metadata in RDMDraft.model_cls.query.offset(100*page).limit(100).filter_by(id.not_in(page_error)):
                draft = RDMDraft(draft_metadata.data, model=draft_metadata)
                update_record(draft)
        db.session.commit()

    success = not errors

    if success:
        secho("Commiting to DB", nl=True)
        db.session.commit()
        secho(
            "Data migration completed, please rebuild the search indices now.",
            fg="green",
        )

    else:
        secho("Rollback", nl=True)
        db.session.rollback()
        secho(
            "Upgrade aborted due to the following errors:",
            fg="red",
            err=True,
        )

        for error in errors:
            secho(error, fg="red", err=True)

        msg = (
            "The changes have been rolled back. "
            "Please fix the above listed errors and try the upgrade again",
        )
        secho(msg, fg="yellow", err=True)

        sys.exit(1)


def migrate_record(i_record_id):
    secho(f"Starting record migration for record {i_record_id}", fg="green")
    a_specific_record = None
    try:
        a_specific_record = RDMRecord.pid.resolve(i_record_id)
    except BaseException as e:
        secho(f"Not a record, trying draft: {i_record_id}", fg="yellow")
        a_specific_record = RDMDraft.pid.resolve(i_record_id)
    if not a_specific_record:
        secho(f"Record not found: {i_record_id}", fg="yellow")
        return
    error = update_record(a_specific_record)
    if not error:
        db.session.commit()


def migrate_record_list_from_file(i_file_path):
    secho(f"Starting record list migration from: {i_file_path}", fg="green")
    with open(i_file_path, 'r') as file:
        for it_line in file.readlines():
            #if re.match(r"[0-9a-z]+-[0-9a-z]+", it_line):
            migrate_record(it_line.strip())
            #else:
            #    print(f"Not a record: {it_line}")


def main(i_file=None, i_record=None):
    if i_record is not None:
        migrate_record(record)
    elif i_file is not None and os.path.isfile(i_file):
        migrate_record_list_from_file(i_file)
    else:
        execute_upgrade()



# if the script is executed on its own, perform the upgrade
if __name__ == "__main__":
    main("./record_to_upgrade.tmp")

// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// InvenioRDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_app_rdm/i18next";
import React, { Component } from "react";
import PropTypes from "prop-types";
import { Header, Modal, Button } from "semantic-ui-react";
import { PendingCommunitiesSearch } from "./PendingCommunitiesSearch";
import { CommunityType } from "@js/invenio_communities";

export class PendingCommunitiesModal extends Component {
  render() {
    const {
      searchConfig,
      modalOpen,
      successActionCallback,
      handleOnOpen,
      handleOnClose,
      communityType,
    } = this.props;

    return (
      <Modal
        role="dialog"
        aria-labelledby="record-communities-header"
        id="community-selection-modal"
        closeIcon
        closeOnDimmerClick={false}
        open={modalOpen}
        onClose={handleOnClose}
        onOpen={handleOnOpen}
      >
        <Modal.Header>
          <Header as="h2" size="small" id="record-communities-header" className="mt-5">
            {i18next.t(`Pending ${communityType.getPlural()}`)}
          </Header>
        </Modal.Header>

        <PendingCommunitiesSearch
          searchConfig={searchConfig}
          successActionCallback={successActionCallback}
          communityType={communityType}
        />

        <Modal.Actions>
          <Button onClick={handleOnClose}>{i18next.t("Close")}</Button>
        </Modal.Actions>
      </Modal>
    );
  }
}

PendingCommunitiesModal.propTypes = {
  searchConfig: PropTypes.object.isRequired,
  modalOpen: PropTypes.bool,
  successActionCallback: PropTypes.func.isRequired,
  handleOnClose: PropTypes.func.isRequired,
  handleOnOpen: PropTypes.func.isRequired,
  communityType: CommunityType,
};

PendingCommunitiesModal.defaultProps = {
  modalOpen: false,
};

# Governance

This document summarizes the **planned** governance model for the OEFAF
platform. It describes intended, conditional arrangements only. The full draft
governance and nonprofit plan is maintained in
[`docs/governance/charter_draft.md`](docs/governance/charter_draft.md).

> All statements in this document are forward-looking and conditional. Nothing
> here should be read as a present-tense claim of incorporation or legal
> status.

## Stewarding organization (planned)

The platform is intended to be governed by the **Open Energy Finance Analytics
Foundation (OEFAF)**, which is **in formation as a Section 501(c)(3) public
charity**. The Foundation is **planned**; its Articles of Incorporation have
**not** been filed. References to the Foundation throughout this repository use
planned and conditional tense ("in formation," "planned," "to be filed," "upon
incorporation").

## Public-interest mission (planned)

OEFAF is being formed to steward the platform as a public-interest resource —
to develop, validate, and openly publish energy-supply and grid-reliability
analytics built entirely on public and openly licensed data, for the benefit of
the public, researchers, agencies, and grid operators.

## Independence and neutrality

- **OEFAF is not controlled by any employer or for-profit entity.**
- **No proprietary or employer intellectual property will be used by the platform.** The platform is
  developed in a clean room using only public and openly licensed data and
  open-source components. No proprietary or employer code, data, dashboards,
  models, parameters, configurations, screenshots, or identifiers are imported,
  referenced as inputs, or used as templates.
- The platform proceeds as a structurally independent public-interest endeavor
  regardless of where any contributor is employed.

## Licensing

All platform code is released under the [MIT License](LICENSE). Bundled sample
data is synthetic illustrative data generated for demonstration and is labeled
as such. The open-source licensing posture is intended to maximize public
reuse, reproducibility, and independent verification.

## Planned board and advisory structure

Upon incorporation, OEFAF is planned to be directed by a board of directors and
supported by a technical advisory committee. The planned structure is intended
to include:

- A **board of directors** responsible for fiduciary oversight, mission
  alignment, and approval of major policies.
- A **technical advisory committee** drawn from universities, agencies,
  ISOs/RTOs, and independent researchers, providing methodology and validation
  guidance.
- Conflict-of-interest safeguards and neutrality policies governing board,
  advisory, and maintainer roles.

The detailed composition, recruitment plan, and bylaws are described in the
draft governance charter and remain subject to confirmation upon
incorporation.

## Contribution, code-review, and security-review policy

- **Contribution.** Outside contributors (universities, agencies, ISOs/RTOs,
  regulators, and independent researchers) are welcomed under the rules in
  [`CONTRIBUTING.md`](CONTRIBUTING.md). All contributions must use public or
  openly licensed inputs and be developed clean-room.
- **Code review.** Every change receives at least one maintainer code review
  covering correctness, reproducibility, schema conformance, and the
  clean-room / public-data-only rule.
- **Security review.** Changes to the API surface, data ingestion, or
  dependency manifests receive an additional security review covering input
  validation, dependency provenance, and the absence of any non-public data
  paths.
- **Data governance.** The platform consumes public and openly licensed data
  only. Bundled fixtures are synthetic and labeled. The public data-source
  inventory is maintained at
  [`shared/data_sources/sources.yaml`](shared/data_sources/sources.yaml) and
  [`docs/data_inventory/sources.md`](docs/data_inventory/sources.md).

## Cross-reference

The full draft governance and nonprofit plan — including the planned
incorporation roadmap, board and advisory composition, conflict-of-interest
policy, and bylaws — is maintained in the draft governance charter at
[`docs/governance/charter_draft.md`](docs/governance/charter_draft.md). This
document is a high-level summary; the charter draft controls where the two differ.

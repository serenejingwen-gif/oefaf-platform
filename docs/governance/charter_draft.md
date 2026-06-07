# OEFAF Governance Charter — Draft

> **Status: draft, planned, and conditional.** Every statement in this document
> is forward-looking. Nothing here is a present-tense claim of incorporation or
> legal status. The **Open Energy Finance Analytics Foundation (OEFAF)** is **in
> formation as a Section 501(c)(3) public charity**; its Articles of
> Incorporation have **not** been filed. This charter draft is the high-level
> governance summary for the platform's full draft governance and nonprofit
> plan.

## 1. Mission

OEFAF is being formed to develop, validate, and openly publish energy-supply and
grid-reliability analytics built entirely on public and openly licensed data,
for the benefit of the public, researchers, agencies, and grid operators. The
platform comprises three components:

- **GEA — Geopolitical-Event Analytics:** detection and scoring of
  supply-disruption signals from public sources.
- **CRICAT — Climate-Risk Integrated Capacity-Allocation Toolkit:** power-load
  forecasting and grid-stress / capacity-allocation scenario analysis on public
  ISO/RTO and weather data.
- **SD-MAC — Sector-Wide Deployable Modular Analytics Commons:** the schema
  registry, manifests, and public API that make the platform's analytics
  discoverable, reproducible, and reusable.

## 2. Public-interest purpose

The platform is intended to serve as a public-interest analytics commons. Its
outputs, methods, and code are planned to be openly available so that
universities, agencies, ISOs/RTOs, regulators, and independent researchers can
reproduce, audit, and extend them. The Foundation is being formed to steward
this resource neutrally and in the public interest, independent of any private
commercial interest.

## 3. Planned 501(c)(3) pathway

OEFAF is planned to pursue recognition as a Section 501(c)(3) public charity.
The planned incorporation roadmap is set out in Section 9. Until incorporation,
all references to the Foundation use planned and conditional tense ("in
formation," "planned," "to be filed," "upon incorporation").

## 4. Planned board and advisory structure

Upon incorporation, OEFAF is planned to be directed by a **board of directors**
responsible for fiduciary oversight, mission alignment, and approval of major
policies, supported by a **technical advisory committee** drawn from
universities, agencies, ISOs/RTOs, and independent researchers. The detailed
composition and recruitment plan are described in the draft governance plan and
remain subject to confirmation upon incorporation.

## 5. Conflict-of-interest policy (planned)

The Foundation is planned to adopt a written conflict-of-interest policy
applicable to directors, advisory members, officers, and maintainers. The
planned policy is intended to require disclosure of material interests,
recusal from decisions where a conflict exists, and documentation of the basis
for decisions involving potentially conflicted parties. The policy is intended
to reinforce the platform's neutrality and independence — in particular:

- **OEFAF is not controlled by any employer or for-profit entity.**
- **No proprietary or employer intellectual property will be used by the platform.**

## 6. Open-source (MIT) licensing plan

All platform code is planned to be released under the [MIT License](../../LICENSE).
Bundled sample data is synthetic illustrative data generated for demonstration
and is labeled as such. The open-source posture is intended to maximize public
reuse, reproducibility, and independent verification.

## 7. Contribution, code-review, security-review, and data-governance policy

- **Contribution.** Outside contributors are welcomed under the rules in
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md). Contributions must use public or
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
  [`shared/data_sources/sources.yaml`](../../shared/data_sources/sources.yaml)
  and [`docs/data_inventory/sources.md`](../data_inventory/sources.md).

## 8. Documentation and model-auditability standards (planned)

The Foundation is planned to adopt documentation and auditability standards
intended to ensure that every published model and analytic is reproducible from
public inputs. Planned standards include:

- A public schema registry (`sdmac/schema_registry/`) defining all record types.
- Module manifests (`sdmac/manifests/`) declaring each module's component,
  license, dependencies, data inputs, outputs, and validation status.
- Companion notebooks demonstrating each component's methodology on synthetic
  or public-illustrative data.
- A validation roadmap (`docs/validation_roadmap/`) describing the public
  benchmarks, metrics, and target thresholds against which the platform is
  planned to be validated.

## 9. Planned incorporation roadmap

The following steps are planned and conditional; none asserts a present-tense
legal status:

1. **Name search** — confirm availability of the Foundation's name.
2. **Articles of Incorporation** — draft and file articles establishing the
   Foundation as a nonprofit corporation.
3. **Bylaws** — adopt bylaws governing board, officer, and committee roles.
4. **EIN** — obtain an Employer Identification Number.
5. **501(c)(3) application** — prepare and submit the federal tax-exemption
   application.
6. **Advisory recruitment** — recruit the technical advisory committee from
   universities, agencies, ISOs/RTOs, and independent researchers.
7. **Public repository launch** — publish the platform repository under the
   Foundation's planned public governance.

## 10. Cross-reference

The full draft governance and nonprofit plan — including detailed board and
advisory composition, the conflict-of-interest policy, bylaws, and the
incorporation roadmap — is captured across this charter draft and the
high-level summary maintained in [`GOVERNANCE.md`](../../GOVERNANCE.md).

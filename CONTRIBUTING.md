# Contributing to the OEFAF platform

Thank you for your interest in contributing. The platform is being developed in
the open as a public-interest project, intended for public release under the
governance of the Open Energy Finance Analytics Foundation (OEFAF), which is in
formation as a Section 501(c)(3) public charity. See [`GOVERNANCE.md`](GOVERNANCE.md)
for the planned governance model and
[`docs/governance/charter_draft.md`](docs/governance/charter_draft.md) for the
full draft governance and nonprofit plan.

> **Note on bundled data.** All datasets bundled in this repository are
> synthetic illustrative data generated for demonstration. They are NOT real
> agency data and NOT derived from any proprietary or employer source.

## Who we hope to work with

The platform is intended to serve and be improved by a broad public community,
including:

- Universities and academic research groups.
- Federal and state agencies.
- Independent System Operators and Regional Transmission Organizations
  (ISOs/RTOs).
- Energy and reliability regulators.
- Independent researchers and open-source contributors.

If you represent one of these communities and would like to discuss a larger
collaboration, please open an issue describing the proposed work.

## The clean-room, public-data-only rule (non-negotiable)

Every contribution MUST satisfy the following:

1. **Public or openly licensed inputs only.** Code, schemas, fixtures, and
   notebooks may consume only public or openly licensed data and open-source
   components. Do not contribute, reference as an input, or use as a template
   any proprietary, confidential, employer-internal, or otherwise non-public
   code, data, dashboards, models, parameters, configurations, screenshots, or
   identifiers.
2. **Clean-room development.** Contributions must be developed independently
   from any proprietary system. Prior institutional experience may inform
   methodology at the level of capability and approach only.
3. **Honest synthetic labeling.** Any bundled sample data must carry a header
   or README stating that it is synthetic illustrative data generated for
   demonstration, not real agency data, and not derived from any proprietary or
   employer source.
4. **License compatibility.** All contributed code is accepted under the
   project's [MIT License](LICENSE). By contributing, you agree your
   contribution may be distributed under that license.

Contributions that cannot meet these conditions cannot be accepted.

## How to contribute

1. **Open an issue first** for any non-trivial change, so the approach can be
   discussed before implementation.
2. **Fork and branch.** Create a topic branch for your change.
3. **Develop and test.** Add or update tests under the relevant component's
   `tests/` directory. Run the local checks:

   ```bash
   make setup    # create the reproducible environment
   make lint     # ruff
   make test     # pytest across gea / cricat / sdmac
   ```

4. **Document.** Update the relevant `docs/` pages and component READMEs.
5. **Open a pull request** describing the change, the public data sources used
   (if any), and how you verified the clean-room and public-data-only rules.

## Code review

Every pull request receives at least one maintainer code review. Reviews check:

- Correctness, test coverage, and reproducibility (seeded, offline, runnable on
  Python 3.12).
- Compliance with the clean-room and public-data-only rule above.
- Schema conformance for any record types defined in
  `sdmac/schema_registry/`.

## Security review

Changes that touch the API surface (`sdmac/api/`), data ingestion, or
dependency manifests receive an additional security review covering input
validation, dependency provenance, and the absence of any non-public data
paths. Report suspected security issues privately to
`<JING_WEN_TO_FILL: security contact email>` rather than opening a public issue.

## Code of Conduct

All participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).

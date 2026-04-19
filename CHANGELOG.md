# Changelog

All notable changes to NormTrace-IHR are documented here. The versioning scheme follows semantic versioning: major versions indicate changes to the analytical methodology that would produce different results for the same corpus; minor versions indicate additions to country reference files or corpus discovery logic; patch versions indicate bug corrections and interface improvements.

---

## [1.0.0] -- 2025

Initial release.

**Analytical framework**

- Four-link enablement chain (norm, actor, authority, enforceability) applied to 29 selected IHR provisions
- Seven analytical blocks (A through G) covering institutional architecture, core capacities, points of entry, measures on persons and goods, data and documents, additional measures and accountability, and inverse compatibility
- C1 normative score on a 1-to-5 scale, comparable with the WHO e-SPAR
- Weak-link rule: any indicator scoring 1 caps the weighted aggregate at 2.5

**Country references**

- Mexico (initial reference case)
- Switzerland (initial reference case)
- Generic civil law template

**Application**

- Automated corpus discovery across eight sectors
- User corpus validation step before analysis begins
- Block-by-block analysis with streaming output
- Source traceability: consultation date and last-reform date stored per instrument
- Output language configurable per analysis (English, Spanish, French)
- Interface language independent of output language

**Related versions**

- NormTrace-CRPD (disability rights, Mexico pilot): Zenodo DOI listed in CITATION.cff

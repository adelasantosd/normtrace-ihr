# Contributing to NormTrace-IHR

NormTrace-IHR is a research tool under active development. Contributions are welcome and should follow the principles described here.

---

## What kinds of contributions are useful

**Country normative references.** The most immediately useful contributions are country reference files for countries not yet covered in the `backend/` directory. A reference file documents the country's legal system type, hierarchy of norms, official legislative repositories, key sectoral laws and their URLs, and the distribution of competences in federal systems. The format is described in the existing reference files under `docs/country-references/`.

**Corrections to analytical criteria.** If you identify an IHR provision that should be included in or excluded from the selected set, or a flaw in the application of the four-link enablement chain to a specific provision, please open an issue describing the provision, the current classification, your proposed classification, and the methodological justification. Changes to the analytical criteria alter the results the tool produces and therefore require explicit documentation in `METHODOLOGY.md`.

**Prompt corrections.** The analytical prompts in `backend/skill_prompt.py` encode the methodology. If you identify a discrepancy between the documented methodology and the prompts, please open an issue with the specific discrepancy. Changes to prompts should be accompanied by an update to `METHODOLOGY.md` and a version increment.

**Bug reports.** Please describe the issue, the steps to reproduce it, and the expected versus actual behaviour. Include the version number.

**Translations.** The interface translation files are in `frontend/src/i18n/locales/`. If you add a language, please ensure that legal terminology is rendered in the formal register appropriate to legal documents in that language.

---

## What to avoid

Do not open pull requests that change the analytical methodology without first opening an issue and reaching agreement on the change. Methodology changes have implications for reproducibility across published analyses.

Do not add country-specific normative findings to the shared reference files on the basis of secondary sources alone. All entries in country reference files should be traceable to official legal texts, with URLs to official repositories.

---

## Process

1. Open an issue describing the proposed contribution.
2. Wait for acknowledgement before beginning significant work.
3. Fork the repository, make your changes in a named branch, and open a pull request referencing the issue.
4. Ensure that any changes to `backend/skill_prompt.py` are reflected in `METHODOLOGY.md`.
5. Ensure that any changes to the database schema are reflected in the migration files and in the schema documentation.

---

## Attribution

Contributors will be acknowledged in `CHANGELOG.md` alongside the changes they contributed. The `CITATION.cff` file lists the primary author; contributions that rise to the level of co-authorship (substantial changes to the methodology, major new country coverage, or publication-level analyses) will be discussed on a case-by-case basis.

---

## Code of conduct

This is a research tool used in policy-relevant contexts. Contributions should be made in good faith, with accuracy and methodological rigour as the primary criteria. Political considerations about how a country's legal framework should be evaluated are not grounds for changing the analytical criteria.

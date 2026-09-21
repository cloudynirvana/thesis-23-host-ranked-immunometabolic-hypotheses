# Host infection windows that re-rank immunometabolic hypothesis structures without entering Θ

**Thesis #23.** Computational research, set out in Nile University B.Sc. chapter order for handoff. Depends on Thesis #10 and Thesis #14.

**Author:** Kelechi Emeka Ogbonna  
**Email:** kelechiogbonna300@gmail.com  
**GitHub:** https://github.com/cloudynirvana  
**Date:** 21 September 2026

Can declared infection/host delay windows change the rank order of immunometabolic hypothesis structures while both the windows and the immunometabolic non-parameters stay outside Θ?

Five structure records share a frozen kinetic vector Θ of length 7. The ranker does not read it. Immunometabolic evidence is a ledger: a tight lactate band, a checkpoint label, and a host supply budget. Host evidence is two declared windows, [1.5, 2.5] and [10, 12]. With the ledger alone the joint key returns U2, U3, U1, U0, U4. Attaching the windows moves the order to U3, U2, U1, U0, U4. A key that ignores the windows still leaves U2 first. A window-only sort that drops the lactate-band mask ranks U4 first; the joint key leaves U4 last. A map that overwrites kinetic supply with the host budget and that adds the ledger constants and k_inf = 1/2, k_host = 1/9 is refused. SHA-256 of the canonical JSON for Θ does not change.

The kinetic literals come from Thesis #10. The window endpoints come from Thesis #14. This deposit does not re-integrate that ODE and does not re-propagate that delay graph. The windows are declared. They are not a cohort.

This is research only. It is not a medical device, not clinical decision support, not a dose, and not a cure. No document DOI is registered.

See [DISCLAIMER.md](DISCLAIMER.md). The manuscript is [THESIS.md](THESIS.md).

## Files

| Path | Role |
| --- | --- |
| `THESIS.md` | Manuscript (Chapters 1 to 5, Vancouver citations) |
| `THESIS.pdf` | PDF built from the Markdown |
| `build_pdf.py` | Regenerates `THESIS.pdf` |
| `CITATION.cff` | Citation metadata, no document DOI |
| `DISCLAIMER.md` | Research-only boundary |
| `sim/joint_rank.py` | Seeded joint rank and refusal (seed 20260921) |
| `sim/results.json` | Orders, digest, and the refused proposal cited in Chapter Four |
| `sim/figures/` | Rank change, unhosted counts, refusal |

## Reproduce

```bash
python3 -m pip install -r sim/requirements.txt
python3 sim/joint_rank.py
python3 build_pdf.py
```

NumPy and Matplotlib are required for the rank and the figures. The PDF step also needs the `markdown` and `weasyprint` packages. Regenerating the script rewrites `sim/results.json` and `sim/figures/`.

## Cite

Ogbonna KE. Host infection windows that re-rank immunometabolic hypothesis structures without entering Θ [Internet]. Thesis #23 computational research thesis. 21 September 2026 [cited YYYY Mon DD]. Available from: https://github.com/cloudynirvana/thesis-23-host-ranked-immunometabolic-hypotheses

Machine-readable fields are in `CITATION.cff`. Add a document DOI there only after one exists.

Hub index, for cataloguing only: [research-theses-hub](https://github.com/cloudynirvana/research-theses-hub).

Depends on: [Thesis #10](https://github.com/cloudynirvana/thesis-10-immunometabolic-refuse-as-parameter), [Thesis #14](https://github.com/cloudynirvana/thesis-14-infection-residual-burden-delay-graph).

## Licence

Text and sketch code are MIT, with attribution. Computational research only.

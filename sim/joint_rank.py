#!/usr/bin/env python3
"""Joint rank of immunometabolic structures under host windows.

Research sketch only. The ranker reads structure records and two evidence
schedules. It does not integrate an ODE, propagate a delay graph, or read Θ.
A guard refuses any write of ledger constants or window-derived keys into Θ.

Seed 20260921 is used only for an order-stability audit.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
SEED = 20260921

# Frozen kinetic names. Values are the declared legal vector of Thesis #10.
# They are not estimated here, and the ranker does not receive them.
THETA = {
    "r": 0.3,
    "K": 1.2,
    "kappa": 0.5,
    "sigma": 0.12,
    "delta": 0.25,
    "pi": 0.7,
    "lam": 0.55,
}

# Immunometabolic non-parameters. Inherited declarations from Thesis #10.
# They adjudicate admissibility and are not members of Θ.
LEDGER = {
    "phi": 0.55,
    "sigma_host": 0.20,
    "L_lo": 0.0,
    "L_hi": 0.45,
    "checkpoint": "present",
    "band": "tight",
}

# Host windows. Inherited declarations from Thesis #14.
# They are evidence intervals, not delay-graph edges and not rates.
WINDOWS = {
    "W_I": {"lo": 1.5, "hi": 2.5, "label": "infection"},
    "W_M": {"lo": 10.0, "hi": 12.0, "label": "marrow_stress"},
}

IMMUNO_EVIDENCE = ("E_lac", "E_ck", "E_sup")

# Structure records. Flags and slots are syntax. They are not integrator output.
STRUCTURES = (
    {
        "id": "U0",
        "name": "open_baseline",
        "immuno_slots": (),
        "window_slots": (),
        "inside_lactate_band": True,
        "within_supply_budget": True,
        "checkpoint_ok": True,
    },
    {
        "id": "U1",
        "name": "lactate_masked",
        "immuno_slots": ("E_lac", "E_sup"),
        "window_slots": (),
        "inside_lactate_band": True,
        "within_supply_budget": True,
        "checkpoint_ok": True,
    },
    {
        "id": "U2",
        "name": "checkpoint_scaled",
        "immuno_slots": ("E_lac", "E_ck", "E_sup"),
        "window_slots": (),
        "inside_lactate_band": True,
        "within_supply_budget": True,
        "checkpoint_ok": True,
    },
    {
        "id": "U3",
        "name": "windowed_checkpoint",
        "immuno_slots": ("E_lac", "E_ck", "E_sup"),
        "window_slots": ("W_I", "W_M"),
        "inside_lactate_band": True,
        "within_supply_budget": True,
        "checkpoint_ok": True,
    },
    {
        "id": "U4",
        "name": "band_bypass",
        "immuno_slots": ("E_ck",),
        "window_slots": ("W_I", "W_M"),
        "inside_lactate_band": False,
        "within_supply_budget": True,
        "checkpoint_ok": True,
    },
)

SCHEDULES = {
    "immuno_only": {"windows": ()},
    "host": {"windows": ("W_I", "W_M")},
}


def canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256(obj: dict) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def admissible(structure: dict) -> bool:
    return bool(
        structure["inside_lactate_band"]
        and structure["within_supply_budget"]
        and structure["checkpoint_ok"]
    )


def score_row(structure: dict, window_ids: tuple[str, ...]) -> dict:
    immuno_slots = set(structure["immuno_slots"])
    window_slots = set(structure["window_slots"])
    unexplained_immuno = [item for item in IMMUNO_EVIDENCE if item not in immuno_slots]
    unexplained_windows = [item for item in window_ids if item not in window_slots]
    reasons = []
    if not structure["inside_lactate_band"]:
        reasons.append("lactate_outside_host_band")
    if not structure["within_supply_budget"]:
        reasons.append("supply_above_host_budget")
    if not structure["checkpoint_ok"]:
        reasons.append("checkpoint_slot_without_label")
    return {
        "id": structure["id"],
        "name": structure["name"],
        "admissible": admissible(structure),
        "reasons": reasons,
        "immuno_slots": list(structure["immuno_slots"]),
        "window_slots": list(structure["window_slots"]),
        "n_slots": len(structure["immuno_slots"]) + len(structure["window_slots"]),
        "unexplained_immuno": unexplained_immuno,
        "n_unexplained_immuno": len(unexplained_immuno),
        "unexplained_windows": unexplained_windows,
        "n_unexplained_windows": len(unexplained_windows),
    }


def key_primary(row: dict) -> tuple:
    """Admissibility, then unhosted windows, then unhosted immunometabolic evidence, then size, then id."""
    return (
        0 if row["admissible"] else 1,
        row["n_unexplained_windows"],
        row["n_unexplained_immuno"],
        row["n_slots"],
        row["id"],
    )


def key_immuno_terms(row: dict) -> tuple:
    """Drops the window term. Used to show that the ledger alone does not move."""
    return (
        0 if row["admissible"] else 1,
        row["n_unexplained_immuno"],
        row["n_slots"],
        row["id"],
    )


def key_windows_as_tiebreak(row: dict) -> tuple:
    """Size before windows. The primary priority is what moves first place."""
    return (
        0 if row["admissible"] else 1,
        row["n_unexplained_immuno"],
        row["n_slots"],
        row["n_unexplained_windows"],
        row["id"],
    )


def key_window_only(row: dict) -> tuple:
    """Drops the immunometabolic mask and the immunometabolic unexplained term."""
    return (
        row["n_unexplained_windows"],
        row["n_slots"],
        row["id"],
    )


def rank_rows(rows: list[dict], key_fn) -> list[dict]:
    ordered = sorted(rows, key=key_fn)
    ranked = []
    for place, row in enumerate(ordered, start=1):
        item = dict(row)
        item["rank"] = place
        ranked.append(item)
    return ranked


def schedule_report(window_ids: tuple[str, ...]) -> dict:
    rows = [score_row(structure, window_ids) for structure in STRUCTURES]
    primary = rank_rows(rows, key_primary)
    return {
        "window_ids": list(window_ids),
        "primary": primary,
        "primary_order": [row["id"] for row in primary],
        "immuno_terms_only_order": [row["id"] for row in rank_rows(rows, key_immuno_terms)],
        "windows_as_tiebreak_order": [row["id"] for row in rank_rows(rows, key_windows_as_tiebreak)],
        "window_only_order": [row["id"] for row in rank_rows(rows, key_window_only)],
    }


def order_stable(window_ids: tuple[str, ...], draws: int = 200) -> dict:
    """The sort key, not the input order, decides the rank."""
    rng = np.random.default_rng(SEED)
    expected = schedule_report(window_ids)["primary_order"]
    discordant = 0
    for _ in range(draws):
        perm = list(STRUCTURES)
        rng.shuffle(perm)
        rows = [score_row(structure, window_ids) for structure in perm]
        order = [row["id"] for row in rank_rows(rows, key_primary)]
        if order != expected:
            discordant += 1
    return {"draws": draws, "discordant": discordant, "expected": expected}


def illegal_proposal() -> dict:
    """Window midpoints and ledger constants offered as if they were Θ. They are not used."""
    mid_i = 0.5 * (WINDOWS["W_I"]["lo"] + WINDOWS["W_I"]["hi"])
    mid_m = 0.5 * (WINDOWS["W_M"]["lo"] + WINDOWS["W_M"]["hi"])
    proposal = dict(THETA)
    proposal["sigma"] = LEDGER["sigma_host"]
    proposal["phi"] = LEDGER["phi"]
    proposal["L_lo"] = LEDGER["L_lo"]
    proposal["L_hi"] = LEDGER["L_hi"]
    proposal["sigma_host"] = LEDGER["sigma_host"]
    proposal["checkpoint"] = LEDGER["checkpoint"]
    proposal["k_inf"] = 1.0 / mid_i
    proposal["k_host"] = 1.0 / (mid_m - mid_i)
    return {
        "mid_I": mid_i,
        "mid_M": mid_m,
        "k_inf_fraction": "1/2",
        "k_host_fraction": "1/9",
        "proposal": proposal,
    }


def guard(proposal: dict, theta: dict) -> dict:
    illegal_keys = sorted(key for key in proposal if key not in theta)
    changed = sorted(key for key in proposal if key in theta and proposal[key] != theta[key])
    if illegal_keys or changed:
        return {
            "status": "REFUSED",
            "code": "ILLEGAL_PROMOTION",
            "illegal_keys": illegal_keys,
            "changed_legal_keys": changed,
            "written_theta": dict(theta),
            "ranker_called": False,
        }
    same = set(proposal) == set(theta) and all(proposal[key] == theta[key] for key in theta)
    if same:
        return {
            "status": "NAMES_UNCHANGED",
            "code": "NO_OP",
            "illegal_keys": [],
            "changed_legal_keys": [],
            "written_theta": dict(theta),
            "ranker_called": False,
        }
    return {
        "status": "REFUSED",
        "code": "ILLEGAL_PROMOTION",
        "illegal_keys": illegal_keys,
        "changed_legal_keys": changed,
        "written_theta": dict(theta),
        "ranker_called": False,
    }


def ranker_reads_theta() -> bool:
    """The rank function's parameters are the evidence rows and a key, never Θ."""
    names = set(inspect.signature(rank_rows).parameters)
    return "theta" in names or "THETA" in names


def plot_ranks(immuno_order: list[str], host_order: list[str]) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    place = {sid: i + 1 for i, sid in enumerate(immuno_order)}
    host_place = {sid: i + 1 for i, sid in enumerate(host_order)}
    colors = {
        "U0": "#6b6b6b",
        "U1": "#3d5a80",
        "U2": "#1b3a4b",
        "U3": "#9b2226",
        "U4": "#b08968",
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for sid in immuno_order:
        ys = [place[sid], host_place[sid]]
        lw = 2.4 if sid in {"U2", "U3"} else 1.5
        ax.plot([0, 1], ys, color=colors[sid], lw=lw, marker="o", ms=6)
        ax.text(-0.06, ys[0], sid, ha="right", va="center", fontsize=10, color=colors[sid])
        ax.text(1.06, ys[1], sid, ha="left", va="center", fontsize=10, color=colors[sid])
    ax.set_xlim(-0.35, 1.35)
    ax.set_ylim(5.4, 0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Immunometabolic ledger only", "Ledger plus host windows"])
    ax.set_ylabel("Rank (1 is first)")
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("Joint key: first place moves from U2 to U3")
    fig.tight_layout()
    fig.savefig(FIG / "rank_change.png", dpi=160)
    plt.close(fig)


def plot_counts(host_rows: list[dict]) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    labels = [row["id"] for row in host_rows]
    windows = [row["n_unexplained_windows"] for row in host_rows]
    immuno = [row["n_unexplained_immuno"] for row in host_rows]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - 0.18, windows, width=0.36, color="#8c3a2f", label="Unhosted host windows")
    ax.bar(x + 0.18, immuno, width=0.36, color="#1f4e79", label="Unhosted immunometabolic evidence")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Count")
    ax.set_ylim(0, 3.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    ax.set_title("Host schedule, before the sort")
    fig.tight_layout()
    fig.savefig(FIG / "unhosted_counts.png", dpi=160)
    plt.close(fig)


def plot_refusal(digest: str, illegal_keys: list[str], changed: list[str]) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.set_axis_off()
    lines = [
        "Guard status: REFUSED    code: ILLEGAL_PROMOTION",
        "Ranker called on the proposal: no",
        "",
        "Θ digest, before the guard and after it",
        digest[:32],
        digest[32:],
        "",
        "Keys the proposal tried to add",
        ", ".join(illegal_keys),
        "",
        "Legal name the proposal tried to edit",
        ", ".join(changed) if changed else "(none)",
        "",
        "Written Θ: the original seven names, original values",
    ]
    ax.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        ha="left",
        family="DejaVu Sans Mono",
        fontsize=9,
        transform=ax.transAxes,
    )
    ax.set_title("Illegal promotion is not a result", loc="left", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "refusal.png", dpi=160)
    plt.close(fig)


def main() -> None:
    if ranker_reads_theta():
        raise SystemExit("ranker must not read theta")

    digest_before = sha256(THETA)
    payload = canonical(THETA)
    reports = {name: schedule_report(tuple(spec["windows"])) for name, spec in SCHEDULES.items()}
    built = illegal_proposal()
    refused = guard(built["proposal"], THETA)
    name_check = guard(dict(THETA), THETA)
    digest_after = sha256(refused["written_theta"])
    stability = {
        name: order_stable(tuple(spec["windows"])) for name, spec in SCHEDULES.items()
    }

    forbidden = [
        "phi",
        "L_lo",
        "L_hi",
        "sigma_host",
        "checkpoint",
        "k_inf",
        "k_host",
        "W_I",
        "W_M",
        "E_lac",
        "E_ck",
        "E_sup",
    ]
    if any(key in THETA for key in forbidden):
        raise SystemExit("non-parameters or windows are inside theta")
    if digest_before != digest_after:
        raise SystemExit("theta digest changed")
    if refused["status"] != "REFUSED" or refused["ranker_called"]:
        raise SystemExit("promotion was not refused")
    if refused["written_theta"] != THETA:
        raise SystemExit("theta was written")
    if name_check["status"] != "NAMES_UNCHANGED":
        raise SystemExit("exact name check failed")
    if reports["immuno_only"]["primary_order"][0] != "U2":
        raise SystemExit("expected U2 first on the immunometabolic schedule")
    if reports["host"]["primary_order"][0] != "U3":
        raise SystemExit("expected U3 first on the host schedule")
    if reports["immuno_only"]["primary_order"] == reports["host"]["primary_order"]:
        raise SystemExit("rank did not change")
    if reports["host"]["immuno_terms_only_order"] != reports["immuno_only"]["primary_order"]:
        raise SystemExit("immunometabolic terms moved under the host schedule")
    if reports["host"]["windows_as_tiebreak_order"][0] != "U2":
        raise SystemExit("tie-break key should leave U2 first")
    if reports["host"]["window_only_order"][0] != "U4":
        raise SystemExit("window-only sort should surface U4")
    if any(block["discordant"] != 0 for block in stability.values()):
        raise SystemExit("rank depended on input order")
    if abs(built["proposal"]["k_inf"] - 0.5) > 1e-12:
        raise SystemExit("k_inf fraction drifted")
    if abs(built["proposal"]["k_host"] - (1.0 / 9.0)) > 1e-12:
        raise SystemExit("k_host fraction drifted")

    host_rows = reports["host"]["primary"]
    plot_ranks(reports["immuno_only"]["primary_order"], reports["host"]["primary_order"])
    plot_counts(host_rows)
    plot_refusal(digest_after, refused["illegal_keys"], refused["changed_legal_keys"])

    results = {
        "seed": SEED,
        "theta": THETA,
        "theta_canonical": payload,
        "theta_digest": digest_after,
        "theta_digest_before_guard": digest_before,
        "theta_digest_unchanged": digest_before == digest_after,
        "ranker_reads_theta": False,
        "forbidden_keys_absent_from_theta": forbidden,
        "ledger": LEDGER,
        "windows": WINDOWS,
        "immuno_evidence": list(IMMUNO_EVIDENCE),
        "structures": [dict(item) for item in STRUCTURES],
        "rank_key": [
            "admissible before inadmissible",
            "fewer unhosted host windows",
            "fewer unhosted immunometabolic evidence objects",
            "fewer slots",
            "structure id",
        ],
        "schedules": {
            name: {
                "window_ids": report["window_ids"],
                "primary_order": report["primary_order"],
                "immuno_terms_only_order": report["immuno_terms_only_order"],
                "windows_as_tiebreak_order": report["windows_as_tiebreak_order"],
                "window_only_order": report["window_only_order"],
                "rows": report["primary"],
            }
            for name, report in reports.items()
        },
        "stability": stability,
        "name_check": name_check,
        "refusal": {
            "status": refused["status"],
            "code": refused["code"],
            "illegal_keys": refused["illegal_keys"],
            "changed_legal_keys": refused["changed_legal_keys"],
            "ranker_called": refused["ranker_called"],
            "written_theta": refused["written_theta"],
            "mid_I": built["mid_I"],
            "mid_M": built["mid_M"],
            "k_inf_fraction": built["k_inf_fraction"],
            "k_host_fraction": built["k_host_fraction"],
            "proposal_not_a_result": built["proposal"],
        },
        "notes": [
            "No ODE was integrated.",
            "No delay graph was propagated.",
            "Windows and immunometabolic non-parameters stay outside theta.",
            "Research only. Not a dose.",
        ],
    }
    # Tuples in structures are not JSON-native until converted above via dict() of the tuples.
    def convert(obj):
        if isinstance(obj, dict):
            return {key: convert(value) for key, value in obj.items()}
        if isinstance(obj, tuple):
            return [convert(value) for value in obj]
        if isinstance(obj, list):
            return [convert(value) for value in obj]
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        return obj

    text = json.dumps(convert(results), indent=2, sort_keys=False)
    (ROOT / "results.json").write_text(text + "\n", encoding="utf-8")
    print(f"immuno_only {reports['immuno_only']['primary_order']}")
    print(f"host        {reports['host']['primary_order']}")
    print(f"tiebreak    {reports['host']['windows_as_tiebreak_order']}")
    print(f"window_only {reports['host']['window_only_order']}")
    print(f"digest      {digest_after}")
    print(f"refused     {refused['illegal_keys']} changed {refused['changed_legal_keys']}")
    print(f"wrote       {ROOT / 'results.json'}")


if __name__ == "__main__":
    main()

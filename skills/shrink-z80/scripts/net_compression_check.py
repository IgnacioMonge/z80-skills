#!/usr/bin/env python3
"""Compute Net_storage vs RAM_peak_delta (hard-contract domain split).

Does not invent sizes — all inputs are explicit CLI numbers from current evidence.

Exit:
  0 always on successful parse (even if net is negative — still a valid report)
  2 on usage error
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    p = argparse.ArgumentParser(
        description="Net_storage / RAM_peak_delta checker for shrink-z80 compress claims"
    )
    p.add_argument("--original", type=int, required=True, help="original asset/section bytes")
    p.add_argument("--packed", type=int, required=True, help="packed payload bytes")
    p.add_argument(
        "--decoder",
        type=int,
        required=True,
        help="full decoder size in bytes (before sharing)",
    )
    p.add_argument(
        "--assets-sharing-decoder",
        type=int,
        default=1,
        help="how many assets share this decoder (default 1)",
    )
    p.add_argument(
        "--call-glue",
        type=int,
        default=0,
        help="extra call-site / glue bytes attributed to this compress path",
    )
    p.add_argument(
        "--workspace",
        type=int,
        default=0,
        help="workspace/scratch bytes if exclusive peak RAM",
    )
    p.add_argument(
        "--workspace-mode",
        choices=("exclusive", "reuse", "overlap"),
        default="exclusive",
        help="exclusive (safe default): counts in RAM_peak; reuse: 0 with lifetime proof; overlap: counts and flags risk",
    )
    p.add_argument(
        "--stack-bss-growth",
        type=int,
        default=0,
        help="additional stack/BSS growth beyond workspace",
    )
    p.add_argument(
        "--pressure-target",
        choices=("storage", "RAM_peak", "resident_total"),
        default="storage",
        help="which net figure is the claim target",
    )
    args = p.parse_args()

    byte_inputs = (
        args.original,
        args.packed,
        args.decoder,
        args.call_glue,
        args.workspace,
        args.stack_bss_growth,
    )
    if any(value < 0 for value in byte_inputs):
        print("error: sizes must be non-negative", file=sys.stderr)
        return 2
    if args.assets_sharing_decoder < 1:
        print("error: --assets-sharing-decoder must be >= 1", file=sys.stderr)
        return 2

    decoder_share = (args.decoder + args.assets_sharing_decoder - 1) // args.assets_sharing_decoder
    decoder_share_exact = args.decoder / args.assets_sharing_decoder
    net_storage = args.original - (args.packed + decoder_share + args.call_glue)

    if args.workspace_mode == "reuse":
        workspace_peak = 0
        ws_note = "reuses existing buffer/screen — not counted; requires lifetime proof"
    elif args.workspace_mode == "exclusive":
        workspace_peak = args.workspace
        ws_note = "exclusive workspace counted"
    else:
        workspace_peak = args.workspace
        ws_note = "OVERLAP — counted as peak risk; do not claim safe resident without lifetime proof"

    ram_peak_delta = workspace_peak + args.stack_bss_growth
    net_resident = net_storage - ram_peak_delta

    print("[net_compression_check]")
    print(f"  original: {args.original}")
    print(f"  packed: {args.packed}")
    print(f"  decoder_full: {args.decoder}")
    print(f"  assets_sharing_decoder: {args.assets_sharing_decoder}")
    print(f"  decoder_share: {decoder_share} (exact_attribution={decoder_share_exact:.2f}, conservative ceil)")
    print(f"  call_glue: {args.call_glue}")
    print(f"  workspace: {args.workspace} mode={args.workspace_mode} ({ws_note})")
    if args.workspace_mode == "reuse" and args.workspace > 0:
        print("  warning: workspace reuse is not proven by arithmetic; verify buffer lifetimes")
    print(f"  stack_bss_growth: {args.stack_bss_growth}")
    print(f"  pressure_target: {args.pressure_target}")
    print()
    print(f"  Net_storage = {args.original} - ({args.packed} + {decoder_share} + {args.call_glue}) = {net_storage}")
    print(f"  RAM_peak_delta = {workspace_peak} + {args.stack_bss_growth} = {ram_peak_delta}")
    print(f"  Net_resident_total = {net_storage:.2f} - {ram_peak_delta} = {net_resident:.2f}")
    print()
    if args.pressure_target == "storage":
        claim = net_storage
        print("  claim_figure: Net_storage (Workspace NOT subtracted)")
    elif args.pressure_target == "RAM_peak":
        claim = -ram_peak_delta  # lower peak is better; report delta
        print("  claim_figure: RAM_peak_delta (positive means more peak RAM)")
    else:
        claim = net_resident
        print("  claim_figure: Net_resident_total (only if lifetimes exclusive)")
        if args.workspace_mode != "exclusive" and args.workspace > 0:
            print(
                "  warning: resident_total with non-exclusive workspace is not EXACTO"
            )
    print(f"  claim_value: {claim:.2f}")
    if net_storage < 0:
        print("  note: negative Net_storage — reject as storage win")
    print(
        "  policy: never report packed%% alone; never fold Workspace into Net_storage "
        "unless pressure_target=resident_total and workspace-mode=exclusive"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

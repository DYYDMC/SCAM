#!/usr/bin/env python3
import argparse
from spec_data_utils import normalize_target_dir, run_optic_filter_and_auc


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ensure scan_data.npz exists, apply optic filter, "
            "and save scan_data_optic_filtered.npz."
        )
    )
    parser.add_argument("target_dir", help="Path like ~/Github/SCAM/one_scam_data/ONE_SCAM_XXXXXX/")
    args = parser.parse_args()

    target_dir = normalize_target_dir(args.target_dir)
    out_npz = run_optic_filter_and_auc(target_dir)
    print(f"[ok] saved: {out_npz}")


if __name__ == "__main__":
    main()

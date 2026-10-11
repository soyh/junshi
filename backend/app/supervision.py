from __future__ import annotations

import argparse
import json

from app.config.settings import get_settings
from app.core.supervision import SupervisionContractError, build_supervision_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit the platform-neutral production supervision contract."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        contract = build_supervision_contract(get_settings())
    except SupervisionContractError as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.as_json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"supervision contract error: {exc}")
        return 1

    payload = contract.to_dict()
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("startup gate:", " ".join(payload["startup_gate"]["command"]))
        print("process:", " ".join(payload["process"]["command"]))
        print("liveness:", " ".join(payload["probes"]["liveness"]["command"]))
        print("readiness:", " ".join(payload["probes"]["readiness"]["command"]))
        print("restart policy:", payload["restart"]["policy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

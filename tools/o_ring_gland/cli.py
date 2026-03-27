import argparse
from dataclasses import asdict

from .calculations import ORingInputs, ValidationError, calculate_o_ring_gland


def _prompt_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print("Enter a numeric value.")
            continue
        if value <= 0:
            print("Value must be > 0.")
            continue
        return value


def _prompt_choice(prompt: str, allowed: list[str]) -> str:
    allowed_norm = [item.lower() for item in allowed]
    while True:
        raw = input(prompt).strip().lower()
        if raw in allowed_norm:
            return raw
        print(f"Enter one of: {', '.join(allowed)}")


def _interactive_inputs() -> ORingInputs:
    print("O-ring Gland Calculator (First Pass)")
    print("Units are inches.")

    seal_type = _prompt_choice("Seal type [piston/rod]: ", ["piston", "rod"])
    service_type = _prompt_choice("Service [static/dynamic]: ", ["static", "dynamic"])

    o_ring_id = _prompt_float("O-ring ID: ")
    o_ring_cs = _prompt_float("O-ring cross-section: ")
    groove_width = _prompt_float("Groove width: ")

    if seal_type == "piston":
        bore_diameter = _prompt_float("Bore diameter: ")
        groove_diameter = _prompt_float("Piston groove diameter: ")
        return ORingInputs(
            seal_type=seal_type,
            service_type=service_type,
            o_ring_id=o_ring_id,
            o_ring_cs=o_ring_cs,
            groove_width=groove_width,
            bore_diameter=bore_diameter,
            groove_diameter=groove_diameter,
        )

    rod_diameter = _prompt_float("Rod diameter: ")
    groove_diameter = _prompt_float("Rod groove diameter: ")
    return ORingInputs(
        seal_type=seal_type,
        service_type=service_type,
        o_ring_id=o_ring_id,
        o_ring_cs=o_ring_cs,
        groove_width=groove_width,
        rod_diameter=rod_diameter,
        groove_diameter=groove_diameter,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simple O-ring gland checks for squeeze, stretch, and fill."
    )
    parser.add_argument("--seal-type", choices=["piston", "rod"])
    parser.add_argument("--service-type", choices=["static", "dynamic"])
    parser.add_argument("--o-ring-id", type=float)
    parser.add_argument("--o-ring-cs", type=float)
    parser.add_argument("--groove-width", type=float)
    parser.add_argument("--bore-diameter", type=float)
    parser.add_argument("--rod-diameter", type=float)
    parser.add_argument("--groove-diameter", type=float)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for all inputs in terminal.",
    )
    return parser


def _inputs_from_args(args: argparse.Namespace) -> ORingInputs:
    if not args.seal_type or not args.service_type:
        raise ValidationError("--seal-type and --service-type are required unless using --interactive")

    required = [
        ("o_ring_id", args.o_ring_id),
        ("o_ring_cs", args.o_ring_cs),
        ("groove_width", args.groove_width),
        ("groove_diameter", args.groove_diameter),
    ]
    missing = [name for name, value in required if value is None]
    if missing:
        raise ValidationError("Missing required inputs: " + ", ".join(missing))

    if args.seal_type == "piston" and args.bore_diameter is None:
        raise ValidationError("--bore-diameter is required for piston seals")
    if args.seal_type == "rod" and args.rod_diameter is None:
        raise ValidationError("--rod-diameter is required for rod seals")

    return ORingInputs(
        seal_type=args.seal_type,
        service_type=args.service_type,
        o_ring_id=args.o_ring_id,
        o_ring_cs=args.o_ring_cs,
        groove_width=args.groove_width,
        bore_diameter=args.bore_diameter,
        rod_diameter=args.rod_diameter,
        groove_diameter=args.groove_diameter,
    )


def _print_report(result_dict: dict) -> None:
    print("\nResults")
    print("-------")
    print(f"Radial gland depth:        {result_dict['radial_gland_depth']:.5f} in")
    print(f"Squeeze:                   {result_dict['squeeze_percent']:.2f}%")
    print(f"Stretch:                   {result_dict['stretch_percent']:.2f}%")
    print(f"Gland fill:                {result_dict['fill_percent']:.2f}%")

    print("\nRecommended starting targets")
    print("----------------------------")
    print(f"Target squeeze:            {result_dict['target_squeeze_percent']:.2f}%")
    print(f"Target max fill:           {result_dict['target_fill_percent']:.2f}%")
    print(f"Recommended gland depth:   {result_dict['recommended_gland_depth']:.5f} in")
    print(f"Recommended groove width:  {result_dict['recommended_groove_width_min']:.5f} in (minimum)")
    print(f"Recommended groove dia:    {result_dict['recommended_groove_diameter']:.5f} in")

    warnings = result_dict["warnings"]
    if warnings:
        print("\nWarnings")
        print("--------")
        for note in warnings:
            print(f"- {note}")


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    try:
        if args.interactive:
            inputs = _interactive_inputs()
        else:
            inputs = _inputs_from_args(args)

        result = calculate_o_ring_gland(inputs)
        _print_report(asdict(result))
        return 0
    except ValidationError as exc:
        print(f"Input error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

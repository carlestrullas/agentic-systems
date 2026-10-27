"""
Inspect a product image with a multimodal (vision) agent.

The image is attached with `crew.kickoff(input_files={...})`. It can be a local
path or a public URL, and the model must be able to see images.

Usage:
    python main.py --model gpt-4o-mini
    python main.py --image photos/mug.jpg --product "ceramic mug" --model gpt-4o-mini
    python main.py --image https://example.com/box.jpg --model anthropic/claude-sonnet-4-5
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from llm import build_llm
from models import QualityReport
from quality_crew import QualityCrew

HERE = Path(__file__).parent
OUTPUT_FILE = HERE / "output" / "quality_report.json"

SAMPLE_IMAGE = "https://s.marketwatch.com/public/resources/images/MW-HT101_nerd_d_ZG_20191010165334.jpg"
SEVERITY_ICON = {"low": "🟡", "medium": "🟠", "high": "🔴"}
VERDICT_ICON = {"pass": "✅", "review": "👀", "reject": "⛔"}


def load_image(source: str):
    """Wrap a local path or a URL as an ImageFile (needs `crewai[file-processing]`)."""
    try:
        from crewai_files import ImageFile
    except ImportError:
        raise SystemExit("File inputs need an extra package. Install it with:\n\n    pip install 'crewai[file-processing]'\n")

    if not source.startswith(("http://", "https://")) and not Path(source).is_file():
        raise SystemExit(f"Image not found: {source}")
    return ImageFile(source=source)


def print_report(report: QualityReport) -> None:
    print(f"Product : {report.product}")
    print(f"Score   : {report.quality_score}/10")
    print(f"Verdict : {VERDICT_ICON[report.verdict]} {report.verdict}\n")

    if report.defects:
        print("Defects:")
        for defect in report.defects:
            print(f"  {SEVERITY_ICON[defect.severity]} [{defect.kind}] {defect.description} ({defect.location})")
    else:
        print("No visible defects.")

    print("\nRecommendations:")
    for recommendation in report.recommendations:
        print(f"  - {recommendation}")


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Inspect a product image with a vision agent.")
    parser.add_argument("--image", default=SAMPLE_IMAGE, help="Local path or public URL of the image")
    parser.add_argument("--product", default="product in its shipping box", help="What the image shows")
    parser.add_argument("--model", help="Override the MODEL variable from .env (must be a vision model)")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0)
    if not llm.supports_multimodal():
        raise SystemExit(
            f"'{llm.model}' cannot see images. Use a vision model, e.g. MODEL=gpt-4o-mini, "
            "MODEL=anthropic/claude-sonnet-4-5 or MODEL=gemini/gemini-2.0-flash."
        )

    image = load_image(args.image)
    print(f"🖼️  Inspecting {args.image}\n")

    result = QualityCrew(llm=llm).crew().kickoff(
        inputs={"product": args.product},
        input_files={"product_image": image},  # attached to the model's messages
    )

    report = result.pydantic
    if not isinstance(report, QualityReport):
        raise SystemExit(f"The model did not return a valid report:\n{result.raw}")

    print("\n" + "=" * 60)
    print_report(report)
    print("=" * 60)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"\n✅ Report saved to {OUTPUT_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()

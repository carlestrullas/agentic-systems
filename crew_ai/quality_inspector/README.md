# Quality Inspector (multimodal)

A **multimodal agent**: it looks at a product image, finds visible defects (dents, scratches, misalignment, damaged packaging…) and returns a structured quality report with a score and a ship / review / reject verdict.

```
image (path or URL) ──▶ Product Quality Inspector ──▶ QualityReport ──▶ output/quality_report.json
                         (vision model)               (output_pydantic)
```

Example output (it will vary with the model and the run):

```
Product : cardboard shipping box
Score   : 3/10
Verdict : ⛔ reject

Defects:
  🔴 [dent] Deep dent and creases on the front panel (centre of the box)
  🟠 [misalignment] Sealing tape applied at an angle and peeling (top edge)
  🟠 [packaging] Crushed corner exposing the inner layer (bottom-right corner)

Recommendations:
  - Use double-wall cardboard for this product size.
  ...
```

## How it works

Until now every agent received only text. To let an agent **see**, two things are needed:

1. **A vision model.** `gpt-4o-mini`, Claude and Gemini models accept images; most text models (and the default `llama3.1:8b`) do not. [`main.py`](main.py) checks this with `llm.supports_multimodal()` and stops with a clear message otherwise.
2. **The image attached to the run**, with `input_files`:

```python
from crewai_files import ImageFile

result = QualityCrew(llm=llm).crew().kickoff(
    inputs={"product": "shipping box"},                                 # text placeholders, as always
    input_files={"product_image": ImageFile(source="photos/box.jpg")},  # or a public URL
)
report = result.pydantic   # a QualityReport
```

CrewAI adds the image to the messages sent to the model, in the format each provider expects (inline base64 for small local files, a URL reference when the source is already a URL). The agent and the task in [`quality_crew.py`](quality_crew.py) are ordinary: nothing in them is image-specific, and the task prompt simply refers to "the attached image".

| File | Content |
|---|---|
| [`models.py`](models.py) | `Defect` and `QualityReport`: kind, location and severity of each defect, score (1–10), verdict and recommendations. |
| [`quality_crew.py`](quality_crew.py) | `QualityCrew`, a `@CrewBase` class with one agent and one task that uses `output_pydantic`. |
| [`config/`](config/) | Agent and task prompts in YAML. |
| [`main.py`](main.py) | Command line: loads the image, checks the model can see it, prints and saves the report. |

Files can also be attached to a single task (`Task(..., input_files={...})`) or to a flow (`flow.kickoff(input_files={...})`), and besides `ImageFile` there are `PDFFile`, `AudioFile`, `VideoFile` and `TextFile`. Which types work depends on the provider: images work with all the vision models above, while support for PDFs, audio and video varies (Gemini accepts all of them).

> **`multimodal=True`:** older CrewAI code enables images with `Agent(..., multimodal=True)`, which gives the agent a tool to fetch an image from a URL. That flag is deprecated; `input_files` is the current way and also works with local files.

### Writing good prompts for images

- Say exactly what to look for (here: scratches, dents, misalignment, colour, packaging…) instead of "describe the image".
- Ask the model to describe only what is visible and to return an empty list rather than invent defects; the schema descriptions in `models.py` repeat it.
- Keep images reasonably small: large photos cost more tokens and may exceed provider limits (for example 5 MB per image on Anthropic).

## Setup

```bash
cd crew_ai/quality_inspector
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # installs crewai[file-processing]
cp .env.example .env
```

**Model:** unlike the other examples, the default is a hosted vision model, `gpt-4o-mini`; set `OPENAI_API_KEY` in `.env`, or switch to Claude or Gemini with their key. See [Choosing the model](../README.md#choosing-the-model) for how `MODEL` and the keys work.

**Local (experimental):** CrewAI only sends images to local models it recognises as vision models, such as `llava` or `qwen3-vl`. You can try `ollama pull llava:7b` and `MODEL=ollama/llava:7b`, but small local vision models are much less reliable at spotting defects and at returning valid structured output.

## Run

```bash
# sample image (a damaged shipping box, loaded from a URL)
python main.py

# your own image, local or remote
python main.py --image photos/mug.jpg --product "ceramic mug"
python main.py --image https://example.com/phone.jpg --product "smartphone" --model anthropic/claude-sonnet-4-5
```

The report is printed and saved to `output/quality_report.json` (git-ignored). If the sample URL ever stops working, pass any product photo with `--image`.

## Ideas to extend it

- Inspect a whole folder: loop over the images, run the crew for each and write a CSV with score and verdict per file.
- Add a guardrail that rejects reports whose verdict contradicts the defects (for example `pass` with a high-severity defect); see [`task_features`](../task_features/).
- Attach a reference image of a perfect product as a second file and ask the agent to compare both.

# FinalCheck - PDF Compliance Verification

A Streamlit application that uses LLMs (Large Language Models) with vision capabilities to verify PDF documents for compliance with flammability and labeling standards.

## Features

- Upload PDF documents (limit 10MB)
- Process PDFs by converting each page to images at 90 DPI
- Use vision-based LLMs to perform controlled generation checks
- Verify compliance with various standards:
  - Uniform Law Labels
  - California Flammability Notice (TB117)
  - Labelling Review (16 CFR Part 1640)
  - Flammability Test (16 CFR Part 1631)
- Generate detailed compliance reports

## Installation

1. Clone this repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Set up your environment variables:
```bash
cp .env.example .env
```
5. Edit `.env` and add your OpenAI API key

## Requirements

- Python 3.12+
- OpenAI API key with access to GPT-4 Vision models

## Usage

1. Run the Streamlit app:
```bash
streamlit run run.py
```
2. Open your web browser at http://localhost:8501
3. Upload a PDF file (max 10MB)
4. Select which compliance checks to perform
5. Click "Analyze PDF" button
6. View the results in the three tabs:
   - PDF Preview: View thumbnails of all PDF pages
   - Page Analysis: Detailed analysis of each page
   - Compliance Report: Overall compliance summary

## How It Works

1. The app converts each PDF page to an image at 90 DPI resolution using PyMuPDF
2. Each image is sent to an LLM (GPT-4 Vision) with a structured prompt
3. The LLM analyzes the image for compliance with selected standards
4. Results are compiled into a comprehensive report
5. The app highlights compliant and non-compliant pages

## License

MIT

## TODO
- [x] Change the check box of front page.
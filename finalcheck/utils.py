import base64
import json
import re
from typing import Any, Dict, List, Literal

import openai
from PIL import Image

# Predefined check criteria (based on the image in the prompt)
NAME_MAP = {
    "uniform_law_labels": "Uniform Law Labels",
    "california_flammability": "California Flammability Notice",
    "labelling_review": "Labelling Review (Standard For The Flammability Of Upholstered Furniture – 16 CFR Part 1640)",
    "flammability_test": "Flammability Test (16 CFR Part 1631)",
}

CHECK_CRITERIA = {
    "Uniform Law Labels": {
        "description": """  Law label, need to check,  presence of
            1. Last 4 digits of JAN code
            2. RN
            3. Date of Delivery
        """,
        "standard_name": "uniform_law_labels",
    },
    "California Flammability Notice": {
        "description": """California Flammability Notice, need to check, the “X” is placed in correct option.""",
        "standard_name": "california_flammability",
    },
    "Labelling Review (Standard For The Flammability Of Upholstered Furniture – 16 CFR Part 1640)": {
        "description": """Check compliance with Labelling Review (16 CFR Part 1640). Specifically, check the presence of the following sentences:
        <COMPLIES WITH U.S. CPSC REQUIREMENTS FOR UPHOLSTERED FURNITURE FLAMMABILITY>, if the label contains this sentence, then the product is compliant with the standard.
        """,
        "standard_name": "labelling_review",
    },
    "Flammability Test (16 CFR Part 1631)": {
        "description": """Check compliance with Flammability Test standards (16 CFR Part 1631). Specifically, check the presence of the following sentences:
        <FLAMMABLE (FAILS U.S. DEPARTMENT OF COMMERCE STANDARD FF 2-70): SHOULD NOT BE USED NEAR SOURCES OF IGNITION.>, if the label contains this sentence, then the product is compliant with the standard.
        """,
        "standard_name": "flammability_test",
    },
}


def prepare_image_for_api(image: Image.Image) -> str:
    """Convert PIL Image to base64 string for API submission"""
    import io

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def create_structured_prompt(selected_checks: List[str]) -> str:
    """Create a structured prompt for the LLM based on selected checks"""

    prompt = (
        "Analyze this image and determine compliance with the following standards:\n\n"
    )

    for check in selected_checks:
        if check in CHECK_CRITERIA:
            criteria = CHECK_CRITERIA[check]
            prompt += f"- {criteria['standard_name']}: {criteria['description']}\n"

    prompt += "\nFor each standard, respond in JSON format with these fields:\n"
    prompt += "1. standard_name: Name of the standard\n"
    prompt += "2. is_compliant: true/false\n"
    prompt += "3. content_description: Description of the content in the image you have seen. If you can, try to use markdown table to describe, but in consise for the content which has connection with the standard.\n"

    prompt += """The entire response should be a valid JSON list with one object per standard.
        For example:
        ```json
        [
            {
                "standard_name": "uniform_law_labels",
                "is_compliant": true,
                "content_description": "<the content of Label in concise text>",
            },
            {
                "standard_name": "california_flammability",
                "is_compliant": false,
                "content_description": "<the content in concise text>",
            },
            ...
        ]
        ```
        """

    return prompt


def analyze_page_with_vision_api(
    image: Image.Image,
    selected_checks: List[str],
    detail: Literal["low", "high"] = "high",
) -> Dict[str, Any]:
    """Analyze a single page with the OpenAI Vision API"""
    # Prepare the image
    img_b64 = prepare_image_for_api(image)
    prompt = create_structured_prompt(selected_checks)

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a document compliance verification assistant specialized in product labeling and safety standards. Your task is to analyze document images and determine if they comply with specific regulatory standards.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}",
                            "detail": detail,
                        },
                    },
                ],
            },
        ],
        max_tokens=1500,
    )

    # Extract and parse the JSON response
    json_response = response.choices[0].message.content
    if json_response.startswith("```json"):
        pattern = r"```json(.*)```"
        json_response = re.search(pattern, json_response, re.DOTALL).group(1)

    try:
        result = json.loads(json_response)
        return result
    except json.JSONDecodeError:
        # Fallback in case the LLM doesn't return valid JSON
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": json_response,
        }


def generate_summary_report(page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary report based on all page results"""

    # Initialize summary structure
    summary = {
        "total_pages": len(page_results),
        "checks": {},
        "overall_compliance": True,
        "compliant_pages": 0,
        "non_compliant_pages": 0,
    }

    # Track which checks were performed
    all_checks = set()
    for page_data in page_results:
        if "results" in page_data and isinstance(page_data["results"], list):
            for check in page_data["results"]:
                if "standard_name" in check:
                    all_checks.add(check["standard_name"])

    # Initialize summary for each check
    for check in all_checks:
        summary["checks"][check] = {
            "compliant_pages": [],
            "non_compliant_pages": [],
            "is_overall_compliant": False,
        }

    # Process each page's results
    for page_num, page_data in enumerate(page_results, 1):
        page_compliant = True

        if "results" in page_data and isinstance(page_data["results"], list):
            for check in page_data["results"]:
                if "standard_name" in check and "is_compliant" in check:
                    check_name = check["standard_name"]

                    if check["is_compliant"]:
                        summary["checks"][check_name]["compliant_pages"].append(
                            page_num
                        )
                    else:
                        summary["checks"][check_name]["non_compliant_pages"].append(
                            page_num
                        )
                        page_compliant = False

        if page_compliant:
            summary["compliant_pages"] += 1
        else:
            summary["non_compliant_pages"] += 1

    # Determine overall compliance for each check
    for check in all_checks:
        # A check is compliant overall if there's at least one compliant page
        summary["checks"][check]["is_overall_compliant"] = (
            len(summary["checks"][check]["compliant_pages"]) > 0
        )

        # If any check is non-compliant overall, the document is non-compliant
        if not summary["checks"][check]["is_overall_compliant"]:
            summary["overall_compliance"] = False

    return summary

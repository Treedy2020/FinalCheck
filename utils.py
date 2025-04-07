import base64
import json
from typing import Any, Dict, List

import openai
from PIL import Image

# Predefined check criteria (based on the image in the prompt)
CHECK_CRITERIA = {
    "uniform_law_labels": {
        "description": "Verify if the document contains proper Uniform Law Labels",
        "requirements": [
            "Law label present",
            "Proper formatting of law label",
            "Contains required text about not removing the tag",
            "Material composition information present",
        ],
    },
    "california_flammability": {
        "description": "Check for California Flammability Notice (TB117)",
        "requirements": [
            "TB117 Flammability label present",
            "Contains required warning text",
            "Information about flame retardant chemicals",
            "Properly formatted notice",
        ],
    },
    "labelling_review": {
        "description": "Verify compliance with Labelling Review (16 CFR Part 1640)",
        "requirements": [
            "16 CFR 1640 label present",
            "Complies with U.S. CPSC requirements",
            "Proper formatting of the label",
            "Contains required safety information",
        ],
    },
    "flammability_test": {
        "description": "Check compliance with Flammability Test standards (16 CFR Part 1631)",
        "requirements": [
            "16 CFR 1631 label present",
            "Contains information about flammability status",
            "Warning about sources of ignition",
            "Proper formatting of the warning label",
        ],
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

    prompt = "Analyze this image from a document and determine compliance with the following standards:\n\n"

    for check in selected_checks:
        if check in CHECK_CRITERIA:
            criteria = CHECK_CRITERIA[check]
            prompt += f"- {check}: {criteria['description']}\n"
            prompt += "  Requirements:\n"

            for req in criteria["requirements"]:
                prompt += f"  * {req}\n"

            prompt += "\n"

    prompt += "\nFor each standard, respond in JSON format with these fields:\n"
    prompt += "1. standard_name: Name of the standard\n"
    prompt += "2. is_compliant: true/false\n"
    prompt += "3. findings: List of specific details found on the page\n"
    prompt += "4. missing_elements: List of required elements not found\n\n"

    prompt += (
        "The entire response should be a valid JSON array with one object per standard."
    )

    return prompt


def analyze_page_with_vision_api(
    image: Image.Image, selected_checks: List[str]
) -> Dict[str, Any]:
    """Analyze a single page with the OpenAI Vision API"""

    # Prepare the image
    img_b64 = prepare_image_for_api(image)

    # Create the structured prompt
    prompt = create_structured_prompt(selected_checks)

    # Call the OpenAI API
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
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
                        },
                    },
                ],
            },
        ],
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    # Extract and parse the JSON response
    json_response = response.choices[0].message.content

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

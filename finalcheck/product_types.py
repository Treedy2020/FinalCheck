"""
Product types configuration for compliance checking.
"""

PRODUCT_TYPES = {
    "cushion": {
        "name": {"en": "Cushion", "ja": "クッション"},
        "type": "タプ①",
        "images": ["cushion_blue.jpg", "cushion_grey.jpg", "cushion_world.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "必要",  # Required
            "labelling_review_1640": "必要",  # Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": False,
            "is_furniture": True,
        },
    },
    "mattress_pad": {
        "name": {"en": "Mattress Pad", "ja": "敷きパッド"},
        "type": "タプ②",
        "images": ["mattress_pad_blue.jpg", "mattress_pad_grey.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": True,
            "is_furniture": False,
        },
    },
    "pillow_pad": {
        "name": {"en": "Pillow Pad", "ja": "枕パッド"},
        "type": "タプ②",
        "images": ["pillow_pad_blue.jpg", "pillow_pad_grey.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": True,
            "is_furniture": False,
        },
    },
    "quilt_mat": {
        "name": {"en": "Quilt Mat", "ja": "キルトマット"},
        "type": "タプ②",
        "images": ["quilt_mat_blue.jpg", "quilt_mat_grey.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": True,
            "is_furniture": False,
        },
    },
    "nap_mat": {
        "name": {"en": "Nap Mat", "ja": "お昼寝マット"},
        "type": "タプ②",
        "images": ["nap_mat.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": True,
            "is_furniture": False,
        },
    },
    "floor_mat": {
        "name": {"en": "Floor Mat", "ja": "マット（床に敷く）"},
        "type": "タプ③",
        "images": ["floor_mat.jpg"],
        "requirements": {
            "uniform_law_labels": "必要",  # Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "必要",  # Required
        },
        "criteria": {
            "has_filling": True,
            "thickness_threshold": 0.5,  # inches
            "is_bedding": False,
            "is_floor_covering": True,
            "requires_flame_resistance": True,
        },
    },
    "towel_blanket": {
        "name": {"en": "Towel/Blanket", "ja": "タオルケット・ブランケット"},
        "type": "タプ④",
        "images": ["towel_blue.jpg", "towel_grey.jpg", "blanket.jpg"],
        "requirements": {
            "uniform_law_labels": "不要",  # Not Required
            "california_flammability": "不要",  # Not Required
            "labelling_review_1640": "不要",  # Not Required
            "flammability_test_1631": "不要",  # Not Required
        },
        "criteria": {"has_filling": False, "is_bedding": True, "is_fabric_only": True},
    },
}

# Requirement types and their descriptions
REQUIREMENT_TYPES = {
    "uniform_law_labels": {
        "name": {"en": "Uniform Law Labels", "ja": "Lawラベル"},
        "description": "Basic label requirements for products with filling materials",
        "required_info": [
            "filling_materials",
            "manufacturer_info",
            "warning_text",
            "material_percentages",
            "registration_number",
        ],
    },
    "california_flammability": {
        "name": {
            "en": "California Flammability Notice",
            "ja": "TB117 Flammability ラベル",
        },
        "description": "California specific flammability requirements",
        "required_info": [
            "flammability_performance",
            "flame_retardant_chemicals",
            "safety_statement",
            "california_compliance",
        ],
    },
    "labelling_review_1640": {
        "name": {
            "en": "Labelling Review (16 CFR Part 1640)",
            "ja": "16 CFR 1640ラベル",
        },
        "description": "Federal requirements for upholstered furniture flammability labeling",
        "exemptions": ["thickness_under_0.5_inch", "bedding_products"],
    },
    "flammability_test_1631": {
        "name": {
            "en": "Flammability Test (16 CFR Part 1631)",
            "ja": "16 CFR 1631ラベル",
        },
        "description": "Federal flammability testing requirements for floor coverings",
        "applies_to": ["floor_mats", "carpets", "rugs"],
    },
}

# Status types
STATUS_TYPES = {
    "必要": {"en": "Required", "code": "required", "value": True},
    "不要": {"en": "Not Required", "code": "not_required", "value": False},
}


def get_product_requirements(product_type: str) -> dict:
    """Get the requirements for a specific product type."""
    return PRODUCT_TYPES.get(product_type, {}).get("requirements", {})


def is_requirement_needed(product_type: str, requirement_type: str) -> bool:
    """Check if a specific requirement is needed for a product type."""
    requirements = get_product_requirements(product_type)
    return STATUS_TYPES.get(requirements.get(requirement_type, "不要"), {}).get(
        "value", False
    )


def get_product_criteria(product_type: str) -> dict:
    """Get the criteria for a specific product type."""
    return PRODUCT_TYPES.get(product_type, {}).get("criteria", {})

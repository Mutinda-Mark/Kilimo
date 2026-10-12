"""
Structured tomato disease advisory knowledge.

This module contains the factual advisory information used by
the KILIMO advisory engine.

The information is intentionally kept separate from the NLP
response generation layer so that generated responses do not
become the source of agricultural facts.
"""

DISEASE_KNOWLEDGE = {

    "Bacterial Spot": {
        "description": (
            "A bacterial disease that can cause dark spots on "
            "tomato leaves and fruit."
        ),
        "symptoms": [
            "Small dark spots on leaves",
            "Yellowing around some leaf spots",
            "Spots may also appear on fruit",
        ],
        "management": [
            "Remove badly affected plant material.",
            "Avoid working with plants when foliage is wet.",
            "Improve air circulation between plants.",
            "Use locally recommended disease-management products "
            "where appropriate.",
        ],
        "prevention": [
            "Use clean planting material.",
            "Avoid overhead irrigation where possible.",
            "Remove infected plant debris.",
            "Maintain good spacing between plants.",
        ],
    },

    "Early Blight": {
        "description": (
            "A fungal disease that commonly produces dark leaf "
            "spots and can cause infected leaves to decline."
        ),
        "symptoms": [
            "Dark spots on older leaves",
            "Concentric ring patterns may appear in lesions",
            "Yellowing around affected areas",
            "Progressive loss of affected foliage",
        ],
        "management": [
            "Remove severely affected leaves where practical.",
            "Keep foliage as dry as possible.",
            "Improve airflow around plants.",
            "Remove infected plant debris.",
            "Follow locally approved disease-management guidance.",
        ],
        "prevention": [
            "Rotate crops where practical.",
            "Avoid prolonged leaf wetness.",
            "Maintain adequate plant spacing.",
            "Remove diseased plant material after harvest.",
        ],
    },

    "Late Blight": {
        "description": (
            "A disease that can rapidly affect tomato foliage "
            "under favourable environmental conditions."
        ),
        "symptoms": [
            "Dark or water-soaked appearing leaf lesions",
            "Rapid development of affected areas",
            "Leaf tissue may become extensively damaged",
        ],
        "management": [
            "Inspect nearby tomato plants for similar symptoms.",
            "Remove severely affected plant material where practical.",
            "Reduce prolonged leaf wetness.",
            "Seek locally recommended management guidance promptly.",
        ],
        "prevention": [
            "Monitor plants regularly.",
            "Improve airflow around plants.",
            "Avoid unnecessary leaf wetness.",
            "Remove infected plant debris.",
        ],
    },

    "Leaf Mold": {
        "description": (
            "A fungal disease that primarily affects tomato leaves, "
            "especially under humid conditions."
        ),
        "symptoms": [
            "Yellowish areas on the upper leaf surface",
            "Fungal growth may develop on the underside",
            "Affected leaves may eventually decline",
        ],
        "management": [
            "Improve ventilation around plants.",
            "Reduce excessive humidity where possible.",
            "Remove severely affected leaves.",
            "Follow locally approved disease-management guidance.",
        ],
        "prevention": [
            "Maintain adequate spacing.",
            "Improve airflow.",
            "Avoid unnecessary overhead watering.",
            "Remove infected plant material.",
        ],
    },

    "Septoria Leaf Spot": {
        "description": (
            "A fungal disease that produces numerous small spots "
            "on tomato leaves."
        ),
        "symptoms": [
            "Small circular leaf spots",
            "Dark margins around some lesions",
            "Progressive yellowing and leaf decline",
        ],
        "management": [
            "Remove severely affected leaves.",
            "Remove infected plant debris.",
            "Improve airflow.",
            "Follow locally recommended management practices.",
        ],
        "prevention": [
            "Avoid unnecessary leaf wetness.",
            "Maintain plant spacing.",
            "Remove diseased debris.",
            "Use crop rotation where practical.",
        ],
    },

    "Spider Mites / Two-Spotted Spider Mite": {
        "description": (
            "A pest problem that can cause stippling and weakening "
            "of tomato leaves."
        ),
        "symptoms": [
            "Fine speckling or stippling on leaves",
            "Leaf discoloration",
            "Webbing may be visible in heavier infestations",
        ],
        "management": [
            "Inspect the underside of leaves carefully.",
            "Monitor nearby plants for similar symptoms.",
            "Remove heavily affected plant material where practical.",
            "Use locally recommended pest-management practices.",
        ],
        "prevention": [
            "Monitor plants regularly.",
            "Control weeds that may harbour pests.",
            "Avoid conditions that unnecessarily stress plants.",
        ],
    },

    "Target Spot": {
        "description": (
            "A fungal disease that causes circular lesions on "
            "tomato leaves and can affect fruit."
        ),
        "symptoms": [
            "Circular dark leaf lesions",
            "Target-like patterns may develop",
            "Leaf yellowing and decline",
        ],
        "management": [
            "Remove severely affected leaves.",
            "Reduce prolonged leaf wetness.",
            "Improve airflow around plants.",
            "Follow locally approved disease-management guidance.",
        ],
        "prevention": [
            "Maintain adequate plant spacing.",
            "Remove infected plant debris.",
            "Avoid unnecessary overhead irrigation.",
            "Monitor plants regularly.",
        ],
    },

    "Tomato Yellow Leaf Curl Virus": {
        "description": (
            "A viral disease associated with leaf curling, "
            "yellowing and reduced plant growth."
        ),
        "symptoms": [
            "Upward or inward leaf curling",
            "Yellowing of leaves",
            "Reduced plant growth",
            "Possible reduction in fruit production",
        ],
        "management": [
            "Inspect nearby plants for similar symptoms.",
            "Remove severely affected plants where appropriate.",
            "Control insect vectors using locally recommended practices.",
            "Consult local agricultural extension guidance.",
        ],
        "prevention": [
            "Use healthy planting material.",
            "Monitor and manage insect vectors.",
            "Remove infected plant material.",
            "Control weeds that may harbour vectors.",
        ],
    },

    "Tomato Mosaic Virus": {
        "description": (
            "A viral disease that can produce mosaic patterns "
            "and abnormal leaf development."
        ),
        "symptoms": [
            "Light and dark green mosaic patterns",
            "Leaf distortion",
            "Reduced plant growth",
        ],
        "management": [
            "Remove severely affected plants where appropriate.",
            "Avoid spreading plant sap between plants.",
            "Clean tools used around infected plants.",
            "Seek local agricultural guidance.",
        ],
        "prevention": [
            "Use clean planting material.",
            "Disinfect tools regularly.",
            "Avoid handling healthy plants immediately after infected plants.",
            "Remove infected plant debris.",
        ],
    },

    "Healthy": {
        "description": (
            "The image does not show strong evidence of the supported "
            "tomato diseases."
        ),
        "symptoms": [],
        "management": [
            "Continue regular monitoring.",
            "Maintain good plant nutrition and watering practices.",
            "Inspect plants regularly for new symptoms.",
        ],
        "prevention": [
            "Maintain good field hygiene.",
            "Monitor plants regularly.",
            "Use healthy planting material.",
        ],
    },

    "Powdery Mildew": {
        "description": (
            "A fungal disease that can produce a white powdery "
            "appearance on affected plant surfaces."
        ),
        "symptoms": [
            "White powdery growth",
            "Affected leaf areas may become discoloured",
            "Leaves may decline under heavier infection",
        ],
        "management": [
            "Remove severely affected leaves where practical.",
            "Improve airflow around plants.",
            "Reduce conditions that favour prolonged humidity.",
            "Follow locally approved disease-management guidance.",
        ],
        "prevention": [
            "Maintain adequate spacing.",
            "Improve ventilation.",
            "Monitor plants regularly.",
            "Remove infected plant debris.",
        ],
    },
}
TRANSLATIONS = {
    "vi": {
        "non-helmet": "Không đội mũ bảo hiểm",
        "helmet": "Đội mũ bảo hiểm",
        "motorbike": "Xe máy"
    },
    "en": {
        "non-helmet": "No helmet violation",
        "helmet": "Helmet on",
        "motorbike": "Motorcycle"
    }
}


def format_alert_message(label: str, confidence: float, lang: str = "vi") -> str:
    lang_translations = TRANSLATIONS.get(lang, TRANSLATIONS["vi"])
    localized_label = lang_translations.get(label, label)
    conf_pct = int(confidence * 100)
    
    if lang == "vi":
        return f"Phát hiện {localized_label.lower()} ({conf_pct}%)"
    else:
        return f"Detected {localized_label.lower()} ({conf_pct}%)"

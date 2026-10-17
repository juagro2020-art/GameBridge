import json
import os
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger

class LocalizationManager:
    def __init__(self, locales_dir: str = "locales"):
        self.locales_dir = locales_dir
        self.catalogs: Dict[str, Dict[str, str]] = {}
        self.load_catalogs()

    def load_catalogs(self):
        for locale in settings.SUPPORTED_LOCALES:
            file_path = os.path.join(self.locales_dir, locale, "messages.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.catalogs[locale] = json.load(f)
                    logger.info(f"Loaded {len(self.catalogs[locale])} strings for locale '{locale}'")
                except Exception as e:
                    logger.error(f"Error loading locale '{locale}': {e}")
                    self.catalogs[locale] = {}
            else:
                logger.warning(f"Locale file not found: {file_path}")
                self.catalogs[locale] = {}

    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or settings.DEFAULT_LOCALE
        if loc not in self.catalogs:
            loc = settings.DEFAULT_LOCALE
            
        catalog = self.catalogs.get(loc, {})
        # Fallback to default locale (English) if key is missing in target locale
        text = catalog.get(key)
        if text is None:
            text = self.catalogs.get(settings.DEFAULT_LOCALE, {}).get(key, key)
            
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def check_missing_keys(self) -> Dict[str, list]:
        """Returns missing keys relative to the default locale (canonical)."""
        base_keys = set(self.catalogs.get(settings.DEFAULT_LOCALE, {}).keys())
        missing = {}
        for loc in settings.SUPPORTED_LOCALES:
            if loc == settings.DEFAULT_LOCALE:
                continue
            loc_keys = set(self.catalogs.get(loc, {}).keys())
            diff = list(base_keys - loc_keys)
            if diff:
                missing[loc] = diff
        return missing

i18n = LocalizationManager()

def t(key: str, locale: Optional[str] = None, **kwargs) -> str:
    return i18n.t(key, locale=locale, **kwargs)

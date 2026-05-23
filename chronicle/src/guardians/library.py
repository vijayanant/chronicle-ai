import json
import os
from typing import List, Optional
from pathlib import Path
from .library_models import ReferenceDocument

class ReferenceLibrary:
    """
    The 'Catalog' of seminal works for the Systems Historian.
    Follows a Metadata-First approach.
    """
    def __init__(self, catalog_path: str = "chronicle/data/library/catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self.documents: List[ReferenceDocument] = self._load_catalog()

    def _load_catalog(self) -> List[ReferenceDocument]:
        if not self.catalog_path.exists():
            return []
        with open(self.catalog_path, "r") as f:
            try:
                data = json.load(f)
                return [ReferenceDocument(**doc) for doc in data]
            except:
                return []

    def save_catalog(self):
        with open(self.catalog_path, "w") as f:
            json.dump([doc.model_dump() for doc in self.documents], f, indent=4)

    def add_document(self, doc: ReferenceDocument):
        # Prevent duplicates
        self.documents = [d for doc in self.documents if d.id != doc.id]
        self.documents.append(doc)
        self.save_catalog()

    def search_library(self, query: str) -> List[ReferenceDocument]:
        """
        Simple keyword-based search over metadata for now.
        Can be upgraded to full LanceDB vector search if the library grows large.
        """
        query = query.lower()
        results = []
        for doc in self.documents:
            if (query in doc.title.lower() or 
                query in doc.abstract.lower() or 
                any(query in tag.lower() for tag in doc.tags)):
                results.append(doc)
        return results

from .base import BaseGuardian
from .library import ReferenceLibrary
from chronicle.src.indexer import LibrarianIndexer

class SystemsHistorian(BaseGuardian):
    def __init__(self, indexer: LibrarianIndexer, **kwargs):
        super().__init__(name="historian", **kwargs)
        self.indexer = indexer
        self.library = ReferenceLibrary()

    async def find_historical_context_async(self, concept: str) -> str:
        library_results = self.library.search_library(concept)
        library_context = ""
        if library_results:
            library_context = "SEMINAL REFERENCES:\n" + "\n".join([
                f"- {doc.title} ({doc.year}): {doc.abstract}\n  WHY IT MATTERS: {doc.why_it_matters}" 
                for doc in library_results
            ])

        results = await self.indexer.search(concept, limit=3)
        blog_context = "BLOG HISTORY:\n" + "\n".join([r.chunk.text for r in results])
        
        prompt = f"Analyze the concept: {concept}\n\n{library_context}\n\n{blog_context}\n\nBriefly anchor this concept in historical foundations."
        return await self.ask_local_llm_async(prompt, self.get_mandate())

    def find_historical_context(self, concept: str) -> str:
        library_results = self.library.search_library(concept)
        library_context = ""
        if library_results:
            library_context = "SEMINAL REFERENCES:\n" + "\n".join([
                f"- {doc.title} ({doc.year}): {doc.abstract}\n  WHY IT MATTERS: {doc.why_it_matters}" 
                for doc in library_results
            ])

        results = self.indexer.search(concept, limit=3)
        blog_context = "BLOG HISTORY:\n" + "\n".join([r.chunk.text for r in results])
        
        prompt = f"Analyze the concept: {concept}\n\n{library_context}\n\n{blog_context}\n\nBriefly anchor this concept in historical foundations."
        return self.ask_local_llm(prompt, self.get_mandate())

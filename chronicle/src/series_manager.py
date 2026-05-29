from typing import List, Dict, Any, Optional
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.models import SeriesLedger, NarrativePromise, HandoffBrief, FollowUpSuggestion
from chronicle.src.providers.base import LLMProvider
from datetime import datetime
import json
from .utils.logging import get_logger

logger = get_logger()

class SeriesManager:
    def __init__(self, indexer: LibrarianIndexer, provider: LLMProvider, model_name: str = "deepseek-r1:14b"):
        self.indexer = indexer
        self.provider = provider
        self.model_name = model_name

    async def _extract_promises(self, series_name: str, content_chunks: List[str]) -> List[NarrativePromise]:
        """
        Uses the configured LLM provider to identify future commitments made in the series.
        """
        prompt = f"""
        You are 'The Cartographer'. Analyze these snippets from the '{series_name}' series.
        Identify any commitments the author made to cover a specific topic in a future post.
        (e.g., "In a follow-up, we will explore X", "Later we'll dive into Y").
        
        CONTENT:
        {content_chunks[:30]} 
        
        Output a JSON list of objects with:
        "source_post": (The title of the post where the promise was made),
        "promise_text": (The exact or summarized sentence of the promise),
        "topic": (The core subject of the future post)
        """
        
        response = await self.provider.chat_async(
            model_name=self.model_name,
            messages=[
                {"role": "system", "content": "You are a precise technical editor. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            # Handle potential <think> tags from models like DeepSeek-R1
            clean_content = response
            if "</think>" in clean_content:
                clean_content = clean_content.split("</think>")[-1].strip()
            
            data = json.loads(clean_content)
            promises_raw = data if isinstance(data, list) else data.get("promises", [])
            return [NarrativePromise(**p) for p in promises_raw]
        except Exception as e:
            logger.error(f"Error parsing promises: {e}")
            return []

    async def get_series_ledger(self, series_name: str) -> SeriesLedger:
        """
        Synthesizes a 'Series Ledger' by retrieving all chunks for a series
        and using the configured LLM to summarize them and track promises.
        """
        table = self.indexer.store.get_table()
        # Querying LanceDB via its search API with a filter is more efficient than loading all to pandas
        series_chunks = table.search().where(f"array_contains(series, '{series_name}')").to_list()
        
        if not series_chunks:
            raise ValueError(f"No posts found for series: {series_name}")
            
        unique_posts = sorted(list(set([c['title'] for c in series_chunks])))
        texts = [c['text'] for c in series_chunks]
        
        # 1. Extract Summary and Invariants
        prompt = f"""
        You are 'The Cartographer'. Analyze the '{series_name}' series.
        Posts: {', '.join(unique_posts)}
        
        Provide:
        1. A 3-sentence summary of the narrative arc.
        2. A list of key technical invariants established so far.
        """
        
        response = await self.provider.chat_async(
            model_name=self.model_name,
            messages=[
                {"role": "system", "content": "You are a technical architect."},
                {"role": "user", "content": prompt}
            ]
        )
        
        summary_text = response
        
        # 2. Extract Narrative Promises
        promises = await self._extract_promises(series_name, texts)
        
        return SeriesLedger(
            series_name=series_name,
            posts_count=len(unique_posts),
            last_updated=datetime.now(),
            summary=summary_text,
            open_promises=promises
        )

    async def generate_handoff_brief(self, series_name: str) -> HandoffBrief:
        """
        Analyzes the progression of a series, identifies logical/architectural gaps,
        and recommends deep, significant follow-up topics to write next.
        """
        table = self.indexer.store.get_table()
        series_chunks = table.search().where(f"array_contains(series, '{series_name}')").to_list()
        
        if not series_chunks:
            raise ValueError(f"No posts found for series: {series_name}")
            
        # Group chunks by post title and date to sort chronologically
        posts_data = {}
        for c in series_chunks:
            title = c['title']
            date = c.get('date') or datetime.min
            text = c['text']
            if title not in posts_data:
                posts_data[title] = {"date": date, "chunks": []}
            posts_data[title]["chunks"].append(text)
            
        sorted_posts = sorted(posts_data.keys(), key=lambda x: posts_data[x]["date"])
        last_post_title = sorted_posts[-1] if sorted_posts else "Unknown"
        
        # Build the series progression overview
        progression_lines = []
        handoff_mode = getattr(self.indexer.config, "handoff_mode", "hybrid").lower()
        
        for i, title in enumerate(sorted_posts, 1):
            chunks = posts_data[title]["chunks"]
            
            if handoff_mode == "full":
                full_content = "\n".join(chunks)
                progression_lines.append(f"Post {i}: '{title}'\nFULL CONTENT:\n{full_content}")
            elif handoff_mode == "abstract":
                content_summary = " ".join(chunks[:3])
                progression_lines.append(f"Post {i}: '{title}'\nContent Abstract: {content_summary[:300]}...")
            else:  # hybrid
                is_last_two = (i >= len(sorted_posts) - 1)
                if is_last_two:
                    full_content = "\n".join(chunks)
                    progression_lines.append(f"Post {i}: '{title}'\nFULL CONTENT:\n{full_content}")
                else:
                    content_summary = " ".join(chunks[:3])
                    progression_lines.append(f"Post {i}: '{title}'\nContent Abstract: {content_summary[:300]}...")
        
        progression_text = "\n\n".join(progression_lines)
        
        prompt = f"""
        You are 'The Cartographer' and 'The Adversarial Peer'. 
        Analyze the progression of ideas in the '{series_name}' series.
        
        SERIES PROGRESSION:
        {progression_text}
        
        MANDATE:
        1. Identify Logical Gaps: What technical vulnerabilities, unaddressed trade-offs, or conceptual holes have been created by the progression but not resolved?
        2. Suggest 2 Deep Follow-up Articles: Propose the next logical articles that should be written. For each, provide:
           - Title: A compelling technical title.
           - Rationale: Why this is logically and architecturally the next step.
           - Transition Hook: Suggested opening sentences to link it from the last post ('{last_post_title}').
           
        Output ONLY a JSON object of this shape:
        {{
          "logical_gaps": ["gap 1 description", "gap 2 description"],
          "follow_ups": [
            {{"title": "Compelling Title", "rationale": "Why...", "transition_hook": "How to start..."}}
          ]
        }}
        """
        
        response = await self.provider.chat_async(
            model_name=self.model_name,
            messages=[
                {"role": "system", "content": "You are a precise technical editor and architect. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            clean_content = response
            if "</think>" in clean_content:
                clean_content = clean_content.split("</think>")[-1].strip()
            
            # Strip potential markdown block formatting
            clean_content = clean_content.strip().lstrip("```json").rstrip("```").strip()
            
            data = json.loads(clean_content)
            gaps = data.get("logical_gaps", [])
            follow_ups_raw = data.get("follow_ups", [])
            
            follow_ups = [FollowUpSuggestion(**f) for f in follow_ups_raw]
            return HandoffBrief(
                series_name=series_name,
                last_post_title=last_post_title,
                logical_gaps=gaps,
                follow_ups=follow_ups
            )
        except Exception as e:
            logger.error(f"Error parsing handoff JSON: {e}. Raw response: {response}")
            return HandoffBrief(
                series_name=series_name,
                last_post_title=last_post_title,
                logical_gaps=["Error analyzing series progression gaps."],
                follow_ups=[]
            )

if __name__ == "__main__":
    import asyncio
    from chronicle.src.providers.ollama import OllamaProvider
    
    async def test():
        # Test with project-relative blog root
        config = AppConfig()
        provider = OllamaProvider()
        indexer = LibrarianIndexer(config=config, provider=provider)
        manager = SeriesManager(indexer, provider=provider)
        try:
            ledger = await manager.get_series_ledger("Building Akshara")
            print(f"\n--- Series Ledger: {ledger.series_name} ---")
            print(f"Arc Summary: {ledger.summary}")
            print("\n--- Open Narrative Promises ---")
            for p in ledger.open_promises:
                print(f"- From '{p.source_post}': {p.promise_text} (Topic: {p.topic})")
        except Exception as e:
            print(f"Error: {e}")
            
    asyncio.run(test())

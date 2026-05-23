from .base import BaseGuardian

class SovereignExplorer(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="explorer", **kwargs)

    async def audit_async(self, draft: str) -> str:
        return await self.ask_local_llm_async(f"Audit for sovereignty violations:\n\n{draft}", self.get_mandate())

class MasterCraftsman(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="craftsman", **kwargs)

    async def audit_async(self, draft: str) -> str:
        return await self.ask_local_llm_async(f"Audit for technical discipline:\n\n{draft}", self.get_mandate())

class PragmaticStrategist(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="strategist", **kwargs)

    async def audit_async(self, draft: str) -> str:
        return await self.ask_local_llm_async(f"Audit for pragmatic trade-offs:\n\n{draft}", self.get_mandate())

class Cartographer(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="cartographer", **kwargs)

    async def audit_async(self, draft: str, history_context: str) -> str:
        return await self.ask_local_llm_async(f"Suggest links based on history:\n{history_context}\n\nDRAFT:\n{draft}", self.get_mandate())

class HugoMaster(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="hugo", **kwargs)

    async def audit_async(self, draft: str) -> str:
        return await self.ask_local_llm_async(f"Audit for Hugo/SEO:\n\n{draft}", self.get_mandate())

class Curator(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="curator", **kwargs)

    async def audit_async(self, draft: str) -> str:
        return await self.ask_local_llm_async(f"Evaluate long-term authority:\n\n{draft}", self.get_mandate())

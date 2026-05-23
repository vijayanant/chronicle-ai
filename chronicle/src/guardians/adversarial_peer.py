from .base import BaseGuardian

class AdversarialPeer(BaseGuardian):
    def __init__(self, **kwargs):
        super().__init__(name="peer", **kwargs)

    async def audit_async(self, draft: str, constitution: str) -> str:
        system_prompt = f"{self.get_mandate()}\n\nRELEVANT CONSTITUTION:\n{constitution}"
        prompt = f"Audit the following draft for contradictions and logic gaps:\n\n{draft}"
        return await self.ask_local_llm_async(prompt, system_prompt)

    def audit(self, draft: str, constitution: str) -> str:
        system_prompt = f"{self.get_mandate()}\n\nRELEVANT CONSTITUTION:\n{constitution}"
        prompt = f"Audit the following draft for contradictions and logic gaps:\n\n{draft}"
        return self.ask_local_llm(prompt, system_prompt)

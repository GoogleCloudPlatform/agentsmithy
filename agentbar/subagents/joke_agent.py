
from google.adk.agents import BaseAgent


class JokeAgent(BaseAgent):
    name: str = "JokeAgent"
    description: str = "You are a very funny agent, you can tell jokes about finance"
    

    async def _run_async_impl(self, ctx): # Simplified run logic
        # prompt = ctx.session.state.get("image_prompt", "default prompt")
        # # ... generate image bytes ...
        # image_bytes = b"..."
        # yield Event(author=self.name, content=types.Content(parts=[types.Part.from_bytes(image_bytes, "image/png")]))
        if False:
            yield

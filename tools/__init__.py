from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    slug: str
    name: str
    description: str
    category: str
    blueprint_import: str


# Add new tools here as they are created.
TOOL_REGISTRY = [
    ToolDefinition(
        slug="un-thread-calculator",
        name="UN Thread Calculator",
        description="ASME B1.1 Class 2 thread dimensions with plating adjustments.",
        category="Threading",
        blueprint_import="tools.un_thread.routes:bp",
    )
]

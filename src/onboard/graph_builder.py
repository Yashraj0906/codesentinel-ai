# ============================================================
# graph_builder.py -- Builds a function call graph
# ============================================================
# WHY THIS EXISTS:
# When someone asks "How does login work?", you don't want to
# just return the login() function. You want to show:
#   login() -> validate_credentials() -> hash_password()
#                                     -> check_rate_limit()
#            -> create_session() -> generate_token()
#
# This "call graph" shows the FLOW of the code.
# The QA agent uses it to provide complete answers.
# ============================================================

from dataclasses import dataclass, field
from src.onboard.code_chunker import CodeChunk


@dataclass
class CallGraphNode:
    """One node in the call graph (one function/method)."""
    name: str                               # Function name
    file_path: str                          # Where it lives
    calls: list[str] = field(default_factory=list)     # What it calls
    called_by: list[str] = field(default_factory=list) # What calls it


class GraphBuilder:
    """
    Builds a call graph from code chunks.
    
    WHAT IS A CALL GRAPH:
    A map of "who calls who":
      login() -> validate_credentials() -> hash_password()
    
    WHY IT MATTERS:
    When someone asks about a function, you can trace
    its FULL dependency chain — not just the function itself.
    
    USAGE:
        builder = GraphBuilder()
        graph = builder.build(chunks)
        
        # Get everything login() calls:
        chain = builder.get_call_chain("login", graph, depth=3)
        # Returns: ["login", "validate_credentials", "hash_password", ...]
    """
    
    def build(self, chunks: list[CodeChunk]) -> dict[str, CallGraphNode]:
        """
        Build the call graph from a list of code chunks.
        Returns a dict mapping function names to their graph nodes.
        """
        graph = {}
        
        # Step 1: Create a node for each chunk
        for chunk in chunks:
            if chunk.chunk_type in ("function", "class"):
                graph[chunk.name] = CallGraphNode(
                    name=chunk.name,
                    file_path=chunk.file_path,
                    calls=chunk.calls,
                )
        
        # Step 2: Build reverse edges (called_by)
        # For each function A that calls B, add A to B's called_by list
        all_names = set(graph.keys())
        for name, node in graph.items():
            for called_func in node.calls:
                if called_func in all_names:
                    graph[called_func].called_by.append(name)
        
        print(f"[OK] Built call graph: {len(graph)} nodes")
        return graph
    
    def get_call_chain(
        self,
        function_name: str,
        graph: dict[str, CallGraphNode],
        depth: int = 3,
    ) -> list[str]:
        """
        Get the chain of functions called by a given function.
        Goes `depth` levels deep.
        
        Example:
            get_call_chain("login", graph, depth=2)
            -> ["login", "validate_credentials", "hash_password", "check_rate_limit"]
        """
        visited = set()
        chain = []
        
        def _traverse(name: str, current_depth: int):
            if current_depth > depth or name in visited:
                return
            visited.add(name)
            chain.append(name)
            
            node = graph.get(name)
            if node:
                for called in node.calls:
                    if called in graph:
                        _traverse(called, current_depth + 1)
        
        _traverse(function_name, 0)
        return chain
    
    def get_callers(
        self,
        function_name: str,
        graph: dict[str, CallGraphNode],
    ) -> list[str]:
        """
        Get all functions that call a given function.
        Useful for: "What depends on this function?"
        """
        node = graph.get(function_name)
        if node:
            return node.called_by
        return []
    
    def to_summary(self, graph: dict[str, CallGraphNode]) -> str:
        """
        Generate a human-readable summary of the call graph.
        Used by the QA agent to provide context.
        """
        lines = ["Call Graph Summary:", ""]
        for name, node in sorted(graph.items()):
            outgoing = [c for c in node.calls if c in graph]
            if outgoing:
                lines.append(f"  {name} -> {', '.join(outgoing)}")
            else:
                lines.append(f"  {name} (no outgoing calls)")
        return "\n".join(lines)

import ast
import os
from dataclasses import dataclass, field


@dataclass
class CodeChunk:
    """One chunk of code with its metadata."""
    chunk_id: str                   # Unique ID
    file_path: str                  # e.g., "src/auth/login.py"
    chunk_type: str                 # "function" | "class" | "module"
    name: str                       # Function/class name
    code: str                       # The actual code
    start_line: int
    end_line: int
    docstring: str = ""             # Function/class docstring
    imports: list[str] = field(default_factory=list)   # What this chunk imports
    calls: list[str] = field(default_factory=list)     # Functions this chunk calls
    parent_class: str = ""          # If this is a method, which class it belongs to


class CodeChunker:
    """Splits Python files into semantic chunks (functions, classes, modules) using AST."""
    
    def chunk_file(self, file_path: str, code: str) -> list[CodeChunk]:
        """
        Parse one Python file and return its chunks.
        Each function, class, and module-level block becomes a chunk.
        """
        chunks = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # If the file has syntax errors, treat whole file as one chunk
            if code.strip():
                chunks.append(CodeChunk(
                    chunk_id=f"{file_path}::module",
                    file_path=file_path,
                    chunk_type="module",
                    name=os.path.basename(file_path),
                    code=code,
                    start_line=1,
                    end_line=len(code.split("\n")),
                ))
            return chunks
        
        lines = code.split("\n")
        
        # Extract imports (shared across all chunks in this file)
        imports = self._extract_imports(tree)
        
        # Walk through top-level nodes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                # Extract the whole class as one chunk
                class_code = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                chunks.append(CodeChunk(
                    chunk_id=f"{file_path}::{node.name}",
                    file_path=file_path,
                    chunk_type="class",
                    name=node.name,
                    code=class_code,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node) or "",
                    imports=imports,
                    calls=self._extract_calls(node),
                ))
                
                # Also extract each method separately
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_code = "\n".join(lines[item.lineno - 1 : item.end_lineno])
                        chunks.append(CodeChunk(
                            chunk_id=f"{file_path}::{node.name}.{item.name}",
                            file_path=file_path,
                            chunk_type="function",
                            name=f"{node.name}.{item.name}",
                            code=method_code,
                            start_line=item.lineno,
                            end_line=item.end_lineno or item.lineno,
                            docstring=ast.get_docstring(item) or "",
                            imports=imports,
                            calls=self._extract_calls(item),
                            parent_class=node.name,
                        ))
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_code = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                chunks.append(CodeChunk(
                    chunk_id=f"{file_path}::{node.name}",
                    file_path=file_path,
                    chunk_type="function",
                    name=node.name,
                    code=func_code,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node) or "",
                    imports=imports,
                    calls=self._extract_calls(node),
                ))
        
        # If no functions/classes found, treat whole file as module chunk
        if not chunks and code.strip():
            chunks.append(CodeChunk(
                chunk_id=f"{file_path}::module",
                file_path=file_path,
                chunk_type="module",
                name=os.path.basename(file_path),
                code=code,
                start_line=1,
                end_line=len(lines),
                imports=imports,
            ))
        
        return chunks
    
    def chunk_directory(self, root_dir: str) -> list[CodeChunk]:
        """
        Chunk ALL Python files in a directory (recursive).
        Skips venv, __pycache__, .git, node_modules.
        """
        all_chunks = []
        skip_dirs = {"venv", "__pycache__", ".git", "node_modules", ".tox", "env"}
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip unwanted directories
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            
            for filename in filenames:
                if filename.endswith(".py"):
                    full_path = os.path.join(dirpath, filename)
                    # Use relative path for cleaner IDs
                    rel_path = os.path.relpath(full_path, root_dir)
                    
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            code = f.read()
                        chunks = self.chunk_file(rel_path, code)
                        all_chunks.extend(chunks)
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        print(f"[OK] Chunked {len(all_chunks)} code pieces from {root_dir}")
        return all_chunks
    
    def _extract_imports(self, tree: ast.Module) -> list[str]:
        """Get all import statements from the file."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    def _extract_calls(self, node: ast.AST) -> list[str]:
        """
        Get all function calls made inside a node.
        This is used later to build the call graph.
        """
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))  # Remove duplicates

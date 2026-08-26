"""
tools.py
RUPSHA's hands. She can calculate, run Python, search the web, and tell time.
"""

import warnings
import json
import ast
import operator
import io
import sys
import traceback
import contextlib
from abc import ABC, abstractmethod
from datetime import datetime

# ── Safe import: duckduckgo_search ──
SEARCH_AVAILABLE = False
DDGS = None

try:
    from duckduckgo_search import DDGS as _DDGS
    DDGS = _DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    pass

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════════
# PART 1: BASE CLASS + REGISTRY
# ═══════════════════════════════════════════════════════════════════════

class BaseTool(ABC):
    def __init__(self):
        self.name = "base_tool"
        self.description = "Base tool — do not use directly."
        self.parameters = {}
        self.required_params = []

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass

    def to_groq_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required_params
                }
            }
        }


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        self._tools[tool.name] = tool
        print(f"🔧 Tool registered: {tool.name}")

    def get(self, name):
        return self._tools.get(name)

    def list_tools(self):
        return list(self._tools.keys())

    def to_groq_tools(self):
        return [t.to_groq_schema() for t in self._tools.values()]

    def execute(self, name, arguments):
        tool = self.get(name)
        if not tool:
            return f"❌ Tool '{name}' not found."
        try:
            if isinstance(arguments, dict):
                return tool.execute(**arguments)
            else:
                return tool.execute(arguments)
        except Exception as e:
            return f"❌ Error in '{name}': {str(e)}"


# ═══════════════════════════════════════════════════════════════════════
# PART 2: CONCRETE TOOLS
# ═══════════════════════════════════════════════════════════════════════

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "calculator"
        self.description = (
            "Evaluate math expressions safely. "
            "Examples: '2 + 2', '(5 * 8) / 2', '2 ** 10'"
        )
        self.parameters = {
            "expression": {
                "type": "string",
                "description": "Math expression using +, -, *, /, **, math.sqrt(), etc."
            }
        }
        self.required_params = ["expression"]
        self._allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._allowed_ops:
                raise ValueError(f"Operation not allowed: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._allowed_ops[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._allowed_ops:
                raise ValueError(f"Operation not allowed: {op_type.__name__}")
            return self._allowed_ops[op_type](self._eval_node(node.operand))
        elif isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        else:
            raise ValueError(f"Node type not allowed: {type(node).__name__}")

    def execute(self, expression: str) -> str:
        try:
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree)
            return f"🧮 Result: {result}"
        except Exception as e:
            return f"🧮 Calculator error: {str(e)}"


class PythonExecutorTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "python_executor"
        self.description = (
            "Execute Python code and return printed output. "
            "Use print() to show results."
        )
        self.parameters = {
            "code": {
                "type": "string",
                "description": "Python code to run. Use print() for output."
            }
        }
        self.required_params = ["code"]

    def execute(self, code: str) -> str:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exec_globals = {"__builtins__": __builtins__, "print": print}
            for lib, alias in [
                ("pandas", "pd"), ("numpy", "np"), ("matplotlib.pyplot", "plt"),
                ("scipy", "sp"), ("json", "json"), ("math", "math"),
                ("random", "random"), ("statistics", "statistics"),
            ]:
                try:
                    exec_globals[alias] = __import__(lib)
                except ImportError:
                    pass
            exec(code, exec_globals)
            output = sys.stdout.getvalue()
            return output if output.strip() else "✅ Code ran successfully (no output)."
        except Exception:
            return f"❌ Python Error:\n{traceback.format_exc()}"
        finally:
            sys.stdout = old_stdout


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = (
            "Search the internet using DuckDuckGo. "
            "Returns REAL search results with titles, snippets, and URLs."
        )
        self.parameters = {
            "query": {
                "type": "string",
                "description": "Search query. Be specific."
            },
            "max_results": {
                "type": "integer",
                "description": "How many results (1-5). Default is 3."
            }
        }
        self.required_params = ["query"]

    def execute(self, query: str, max_results=3) -> str:
        if not SEARCH_AVAILABLE:
            return (
                "🔍 Web search unavailable.\n"
                "Run: !pip install -q duckduckgo-search\n"
                "Then restart runtime."
            )

        if not query or not query.strip():
            return "❌ Search query is empty."

        try:
            max_results = int(max_results) if max_results else 3
            max_results = max(1, min(max_results, 5))

            # v7.x: NO backend parameter. Just search.
            with contextlib.redirect_stderr(io.StringIO()):
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return (
                    f"🔍 No results found for: '{query}'\n"
                    f"💡 DuckDuckGo may be rate-limiting this session. Try again later."
                )

            formatted = []
            for i, result in enumerate(results):
                formatted.append(
                    f"{i+1}. {result.get('title', 'No title')}\n"
                    f"   {result.get('body', 'No snippet')}\n"
                    f"   🔗 {result.get('href', 'No link')}"
                )
            return "\n\n".join(formatted)

        except Exception as e:
            return f"❌ Search error: {str(e)}"


class DateTimeTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "datetime"
        self.description = "Get the current date and time."
        self.parameters = {
            "format": {
                "type": "string",
                "description": "Python datetime format string. Default: '%Y-%m-%d %H:%M:%S'"
            }
        }
        self.required_params = []

    def execute(self, format=None) -> str:
        if not format:
            format = "%Y-%m-%d %H:%M:%S"
        return f"🕐 Current time: {datetime.now().strftime(format)}"


# ═══════════════════════════════════════════════════════════════════════
# HELPER: Create the toolkit
# ═══════════════════════════════════════════════════════════════════════

def create_default_toolkit():
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(PythonExecutorTool())
    registry.register(WebSearchTool())
    registry.register(DateTimeTool())
    return registry

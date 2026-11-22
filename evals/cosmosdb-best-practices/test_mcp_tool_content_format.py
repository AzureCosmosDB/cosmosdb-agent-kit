import ast
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest


RULE = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "cosmosdb-best-practices"
    / "rules"
    / "sdk-langchain-mcp-tool-content-format.md"
)


def load_example(section):
    source = RULE.read_text(encoding="utf-8")
    match = re.search(rf"\*\*{section} .*?```python\n(.*?)```", source, re.DOTALL)
    if match is None:
        raise AssertionError(f"Missing {section} Python example in {RULE}")
    tree = ast.parse(match.group(1), filename=str(RULE))
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "extract_routing_info"
    ]
    if len(functions) != 1:
        raise AssertionError(f"Expected one extract_routing_info function in {section}")
    # Exercise the documented function unchanged, without installing LangChain.
    namespace = {"json": json, "ToolMessage": SimpleNamespace}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(RULE), "exec"), namespace)
    return namespace["extract_routing_info"]


class MCPToolContentFormatTests(unittest.TestCase):
    def setUp(self):
        self.extract = load_example("Correct")

    def parse(self, content):
        return self.extract(SimpleNamespace(content=content))

    def test_legacy_string(self):
        self.assertEqual(self.parse('{"goto": "sales"}'), "sales")

    def test_text_blocks(self):
        self.assertEqual(
            self.parse([{"type": "text", "text": '{"goto": "support"}'}]),
            "support",
        )

    def test_non_text_blocks_are_filtered(self):
        self.assertEqual(
            self.parse([
                {"type": "image", "data": "ignored"},
                {"type": "text", "text": '{"goto": "sales"}'},
            ]),
            "sales",
        )

    def test_missing_route_is_not_a_parse_failure(self):
        self.assertIsNone(self.parse('{"status": "complete"}'))

    def test_malformed_json_surfaces(self):
        for content in ("not json", [{"type": "text", "text": "not json"}]):
            with self.subTest(content=content):
                with self.assertRaises(json.JSONDecodeError):
                    self.parse(content)

    def test_no_text_surfaces(self):
        for content in ([], [{"type": "image", "data": "ignored"}]):
            with self.subTest(content=content):
                with self.assertRaises(json.JSONDecodeError):
                    self.parse(content)

    def test_unsupported_top_level_content_surfaces(self):
        for content in (None, 42, {"goto": "sales"}):
            with self.subTest(content=content):
                with self.assertRaises(TypeError):
                    self.parse(content)

    def test_missing_text_value_surfaces(self):
        with self.assertRaises(KeyError):
            self.parse([{"type": "text"}])

    def test_incorrect_example_reproduces_adapter_upgrade_failure(self):
        incorrect = load_example("Incorrect")
        with self.assertRaises(TypeError):
            incorrect(SimpleNamespace(
                content=[{"type": "text", "text": '{"goto": "sales"}'}],
            ))


if __name__ == "__main__":
    unittest.main()

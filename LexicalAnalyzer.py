"""
Simple Lexical Analyzer & Syntax Validator (Mini Project)
--------------------------------------------------------
A GUI tool that tokenizes source code and detects syntax errors
(unclosed quotes, mismatched brackets/parentheses/braces, 
and unclosed/mismatched HTML tags) both live and upon file loading.

Supports C, C++, Java, Python, and HTML.
Built with Python's standard library (tkinter + re).

Run:
    python lexical_analyzer.py
"""

import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ----------------------------------------------------------------------
# 1. THE LEXER & SYNTAX VALIDATION ENGINE
# ----------------------------------------------------------------------

C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "int",
    "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile",
    "while",
}

CPP_KEYWORDS = C_KEYWORDS | {
    "asm", "bool", "catch", "class", "const_cast", "delete", "dynamic_cast",
    "explicit", "export", "false", "friend", "inline", "mutable",
    "namespace", "new", "operator", "private", "protected", "public",
    "reinterpret_cast", "static_cast", "template", "this", "throw", "true",
    "try", "typeid", "typename", "using", "virtual", "wchar_t",
}

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch",
    "char", "class", "const", "continue", "default", "do", "double",
    "else", "enum", "extends", "final", "finally", "float", "for", "goto",
    "if", "implements", "import", "instanceof", "int", "interface", "long",
    "native", "new", "package", "private", "protected", "public", "return",
    "short", "static", "strictfp", "super", "switch", "synchronized",
    "this", "throw", "throws", "transient", "try", "void", "volatile",
    "while", "true", "false", "null",
}

PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield", "match", "case",
}

TOKEN_SPEC_C_CPP = [
    ("COMMENT_ML",       r"/\*.*?\*/"),
    ("UNCLOSED_ML_COMM", r"/\*.*"),
    ("COMMENT_SL",       r"//[^\n]*"),
    ("PREPROCESSOR",     r"#[^\n]*"),
    ("NEWLINE",          r"\n"),
    ("SKIP",             r"[ \t]+"),
    ("FLOAT",            r"\d+\.\d+([eE][+-]?\d+)?[fF]?"),
    ("INTEGER",          r"\d+[uUlL]?"),
    ("STRING",           r'"([^"\\\n]|\\.)*"'),
    ("UNCLOSED_STR",     r'"([^"\\\n]|\\.)*'),
    ("CHAR",             r"'([^'\\\n]|\\.)*'"),
    ("UNCLOSED_CHAR",    r"'([^'\\\n]|\\.)*"),
    ("IDENT",            r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OPERATOR",         r"(==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|"
                          r"<<|>>|->|::|[+\-*/%=<>!&|^~?])"),
    ("PUNCT",            r"[(){}\[\];,.:]"),
    ("MISMATCH",         r"."),
]

TOKEN_SPEC_JAVA = [
    ("COMMENT_ML",       r"/\*.*?\*/"),
    ("UNCLOSED_ML_COMM", r"/\*.*"),
    ("COMMENT_SL",       r"//[^\n]*"),
    ("NEWLINE",          r"\n"),
    ("SKIP",             r"[ \t]+"),
    ("FLOAT",            r"\d+\.\d+([eE][+-]?\d+)?[fF]?"),
    ("INTEGER",          r"\d+[uUlL]?"),
    ("STRING",           r'"([^"\\\n]|\\.)*"'),
    ("UNCLOSED_STR",     r'"([^"\\\n]|\\.)*'),
    ("CHAR",             r"'([^'\\\n]|\\.)*'"),
    ("UNCLOSED_CHAR",    r"'([^'\\\n]|\\.)*"),
    ("IDENT",            r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OPERATOR",         r"(==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|"
                          r"<<|>>|->|::|[+\-*/%=<>!&|^~?])"),
    ("PUNCT",            r"[(){}\[\];,.:]"),
    ("MISMATCH",         r"."),
]

TOKEN_SPEC_PYTHON = [
    ("COMMENT",          r"#[^\n]*"),
    ("NEWLINE",          r"\n"),
    ("SKIP",             r"[ \t]+"),
    ("STRING",           r'("""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'|'
                          r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\')'),
    ("UNCLOSED_TRIPLE",  r'("""|\'\'\').*'),
    ("UNCLOSED_STR",     r'("(?:[^"\\\n]|\\.)*|\'(?:[^\'\\\n]|\\.)*)'),
    ("FLOAT",            r"\d+\.\d+([eE][+-]?\d+)?"),
    ("INTEGER",          r"\d+"),
    ("IDENT",            r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OPERATOR",         r"(\*\*=|//=|==|!=|<=|>=|->|:=|\+=|-=|\*=|/=|%=|&=|\|=|"
                          r"\^=|<<|>>|\*\*|//|[+\-*/%=<>!&|^~@])"),
    ("PUNCT",            r"[(){}\[\]:;,.]"),
    ("MISMATCH",         r"."),
]

VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}


def _compile_spec(spec):
    return re.compile(
        "|".join(f"(?P<{name}>{pattern})" for name, pattern in spec),
        re.DOTALL,
    )


_HTML_OUTER = re.compile(
    r"(?P<COMMENT><!--.*?-->)"
    r"|(?P<DOCTYPE><!DOCTYPE[^>]*>)"
    r"|(?P<TAG><[^>]*>)"
    r"|(?P<UNCLOSED_TAG><[^>]*$)"
    r"|(?P<TEXT>[^<]+)",
    re.DOTALL | re.IGNORECASE,
)

_HTML_INNER = re.compile(
    r"(?P<OPEN></?)"
    r"|(?P<NAME>[A-Za-z][A-Za-z0-9\-]*)"
    r"|(?P<STRING>\"[^\"]*\"|'[^']*')"
    r"|(?P<UNCLOSED_STR>\"[^\"]*|'[^']*)"
    r"|(?P<EQUALS>=)"
    r"|(?P<SLASH>/)"
    r"|(?P<CLOSE>>)"
    r"|(?P<SKIP>\s+)"
    r"|(?P<MISMATCH>.)"
)


def _line_col(source, pos):
    line = source.count("\n", 0, pos) + 1
    last_nl = source.rfind("\n", 0, pos)
    col = pos - last_nl
    return line, col


class Token:
    __slots__ = ("category", "value", "line", "col")

    def __init__(self, category, value, line, col):
        self.category = category
        self.value = value
        self.line = line
        self.col = col


class SyntaxIssue:
    __slots__ = ("message", "line", "col", "length")

    def __init__(self, message, line, col, length=1):
        self.message = message
        self.line = line
        self.col = col
        self.length = length


def tokenize_html(source):
    tokens = []
    errors = []
    tag_stack = []

    for m in _HTML_OUTER.finditer(source):
        kind = m.lastgroup
        text = m.group()
        line, col = _line_col(source, m.start())

        if kind == "TEXT":
            stripped = text.strip()
            if stripped:
                tokens.append(Token("TEXT", stripped, line, col))
            continue
        if kind == "COMMENT":
            tokens.append(Token("COMMENT", text, line, col))
            continue
        if kind == "DOCTYPE":
            tokens.append(Token("TAG", text, line, col))
            continue
        if kind == "UNCLOSED_TAG":
            tokens.append(Token("ERROR", text, line, col))
            errors.append(SyntaxIssue("Unclosed HTML tag (missing '>')", line, col, len(text)))
            continue

        seen_name = False
        current_tag_name = ""
        is_closing = text.startswith("</")
        is_self_closing = text.endswith("/>")

        for im in _HTML_INNER.finditer(text):
            ikind = im.lastgroup
            ival = im.group()
            if ikind == "SKIP" or ival == "":
                continue
            iline, icol = _line_col(source, m.start() + im.start())

            if ikind in ("OPEN", "SLASH", "CLOSE"):
                tokens.append(Token("PUNCTUATION", ival, iline, icol))
            elif ikind == "EQUALS":
                tokens.append(Token("OPERATOR", ival, iline, icol))
            elif ikind == "STRING":
                tokens.append(Token("STRING", ival, iline, icol))
            elif ikind == "UNCLOSED_STR":
                tokens.append(Token("ERROR", ival, iline, icol))
                errors.append(SyntaxIssue("Unclosed string attribute in tag", iline, icol, len(ival)))
            elif ikind == "NAME":
                if not seen_name:
                    tokens.append(Token("TAG", ival, iline, icol))
                    seen_name = True
                    current_tag_name = ival.lower()
                else:
                    tokens.append(Token("ATTRIBUTE", ival, iline, icol))
            elif ikind == "MISMATCH":
                tokens.append(Token("ERROR", ival, iline, icol))
                errors.append(SyntaxIssue(f"Illegal character '{ival}' inside tag", iline, icol, len(ival)))

        if current_tag_name and current_tag_name not in VOID_HTML_TAGS and not is_self_closing:
            if is_closing:
                if not tag_stack:
                    errors.append(SyntaxIssue(f"Unexpected closing tag </{current_tag_name}>", line, col, len(text)))
                else:
                    last_tag, last_line, last_col = tag_stack.pop()
                    if last_tag != current_tag_name:
                        errors.append(SyntaxIssue(
                            f"Mismatched tag: expected </{last_tag}>, found </{current_tag_name}>",
                            line, col, len(text)
                        ))
            else:
                tag_stack.append((current_tag_name, line, col))

    while tag_stack:
        unclosed, uline, ucol = tag_stack.pop()
        errors.append(SyntaxIssue(f"Unclosed HTML tag <{unclosed}>", uline, ucol, len(unclosed) + 2))

    return tokens, errors


CATEGORY_LABELS = {
    "KEYWORD":      "Keyword",
    "IDENTIFIER":   "Identifier",
    "INTEGER":      "Integer Literal",
    "FLOAT":        "Float Literal",
    "STRING":       "String Literal",
    "CHAR":         "Char Literal",
    "OPERATOR":     "Operator",
    "PUNCTUATION":  "Punctuation",
    "PREPROCESSOR": "Preprocessor Directive",
    "TAG":          "Tag",
    "ATTRIBUTE":    "Attribute",
    "TEXT":         "Text",
    "COMMENT":      "Comment",
    "ERROR":        "Syntax / Lexical Error",
}

CATEGORY_COLORS = {
    "light": {
        "KEYWORD": "#0057b8", "IDENTIFIER": "#1b1b1b", "INTEGER": "#a6440d",
        "FLOAT": "#a6440d", "STRING": "#0b8a3d", "CHAR": "#0b8a3d",
        "OPERATOR": "#8a2be2", "PUNCTUATION": "#555555",
        "PREPROCESSOR": "#b8860b", "TAG": "#0057b8", "ATTRIBUTE": "#a6440d",
        "TEXT": "#1b1b1b", "COMMENT": "#8a8a8a", "ERROR": "#d40000",
    },
    "dark": {
        "KEYWORD": "#569cd6", "IDENTIFIER": "#d4d4d4", "INTEGER": "#b5cea8",
        "FLOAT": "#b5cea8", "STRING": "#ce9178", "CHAR": "#ce9178",
        "OPERATOR": "#c586c0", "PUNCTUATION": "#d4d4d4",
        "PREPROCESSOR": "#c586c0", "TAG": "#569cd6", "ATTRIBUTE": "#9cdcfe",
        "TEXT": "#d4d4d4", "COMMENT": "#6a9955", "ERROR": "#f44747",
    },
}

THEMES = {
    "light": {
        "bg": "#f1f5f9", "panel_bg": "#ffffff", "text_fg": "#0f172a",
        "sub_fg": "#475569", "editor_bg": "#ffffff", "editor_fg": "#0f172a",
        "editor_insert": "#000000", "linenum_bg": "#e2e8f0",
        "linenum_fg": "#64748b", "tree_bg": "#ffffff", "tree_fg": "#0f172a",
        "select_bg": "#bfdbfe", "error_bg": "#fee2e2", "jump_bg": "#fef08a",
        "border": "#cbd5e1", "alert_fg": "#dc2626", "ok_fg": "#16a34a",
        "header_bg": "#1e293b", "header_fg": "#ffffff", "header_sub": "#94a3b8",
        "btn_primary":   {"bg": "#2563eb", "fg": "#ffffff", "active": "#1d4ed8"},
        "btn_secondary": {"bg": "#e2e8f0", "fg": "#0f172a", "active": "#cbd5e1"},
        "btn_accent":    {"bg": "#059669", "fg": "#ffffff", "active": "#047857"},
        "btn_danger":    {"bg": "#dc2626", "fg": "#ffffff", "active": "#b91c1c"},
        "btn_toggle":    {"bg": "#334155", "fg": "#ffffff", "active": "#1e293b"},
    },
    "dark": {
        "bg": "#0f172a", "panel_bg": "#1e293b", "text_fg": "#f8fafc",
        "sub_fg": "#94a3b8", "editor_bg": "#141e33", "editor_fg": "#f1f5f9",
        "editor_insert": "#ffffff", "linenum_bg": "#0b1120",
        "linenum_fg": "#64748b", "tree_bg": "#141e33", "tree_fg": "#f8fafc",
        "select_bg": "#1e3a8a", "error_bg": "#450a0a", "jump_bg": "#422006",
        "border": "#334155", "alert_fg": "#f87171", "ok_fg": "#4ade80",
        "header_bg": "#020617", "header_fg": "#f8fafc", "header_sub": "#94a3b8",
        "btn_primary":   {"bg": "#3b82f6", "fg": "#ffffff", "active": "#60a5fa"},
        "btn_secondary": {"bg": "#334155", "fg": "#f8fafc", "active": "#475569"},
        "btn_accent":    {"bg": "#10b981", "fg": "#ffffff", "active": "#34d399"},
        "btn_danger":    {"bg": "#ef4444", "fg": "#ffffff", "active": "#f87171"},
        "btn_toggle":    {"bg": "#38bdf8", "fg": "#020617", "active": "#7dd3fc"},
    },
}

LANGUAGES = {
    "C":      {"keywords": C_KEYWORDS,      "regex": _compile_spec(TOKEN_SPEC_C_CPP)},
    "C++":    {"keywords": CPP_KEYWORDS,    "regex": _compile_spec(TOKEN_SPEC_C_CPP)},
    "Java":   {"keywords": JAVA_KEYWORDS,   "regex": _compile_spec(TOKEN_SPEC_JAVA)},
    "Python": {"keywords": PYTHON_KEYWORDS, "regex": _compile_spec(TOKEN_SPEC_PYTHON)},
    "HTML":   {"html": True},
}

SYMBOL_CATEGORIES = {
    "C": {"IDENTIFIER"}, "C++": {"IDENTIFIER"}, "Java": {"IDENTIFIER"},
    "Python": {"IDENTIFIER"}, "HTML": {"TAG", "ATTRIBUTE"},
}


def tokenize(source: str, language: str = "C"):
    lang = LANGUAGES.get(language, LANGUAGES["C"])
    if lang.get("html"):
        return tokenize_html(source)

    keywords = lang["keywords"]
    regex = lang["regex"]

    tokens = []
    errors = []
    line_num = 1
    line_start = 0

    bracket_stack = []
    bracket_pairs = {")": "(", "}": "{", "]": "["}

    for match in regex.finditer(source):
        kind = match.lastgroup
        value = match.group()
        col = match.start() - line_start + 1

        if kind == "NEWLINE":
            line_num += 1
            line_start = match.end()
            continue
        elif kind == "SKIP":
            continue
        elif kind.startswith("UNCLOSED"):
            tokens.append(Token("ERROR", value, line_num, col))
            desc = kind.replace("UNCLOSED_", "").replace("_", " ").lower()
            errors.append(SyntaxIssue(f"Unclosed {desc}", line_num, col, len(value)))
            newlines = value.count("\n")
            if newlines:
                line_num += newlines
                line_start = match.end() - (len(value) - value.rfind("\n") - 1)
            continue
        elif kind.startswith("COMMENT"):
            newlines = value.count("\n")
            tokens.append(Token("COMMENT", value.strip(), line_num, col))
            if newlines:
                line_num += newlines
                line_start = match.end() - (len(value) - value.rfind("\n") - 1)
            continue
        elif kind == "IDENT":
            category = "KEYWORD" if value in keywords else "IDENTIFIER"
            tokens.append(Token(category, value, line_num, col))
        elif kind == "MISMATCH":
            tokens.append(Token("ERROR", value, line_num, col))
            errors.append(SyntaxIssue(f"Illegal character '{value}'", line_num, col, 1))
        elif kind == "PUNCT":
            tokens.append(Token("PUNCTUATION", value, line_num, col))
            if value in "({[":
                bracket_stack.append((value, line_num, col))
            elif value in ")}]":
                expected = bracket_pairs[value]
                if not bracket_stack:
                    errors.append(SyntaxIssue(f"Unmatched closing bracket '{value}'", line_num, col, 1))
                else:
                    last_b, b_line, b_col = bracket_stack.pop()
                    if last_b != expected:
                        errors.append(SyntaxIssue(
                            f"Mismatched bracket: expected '{last_b}' closer, found '{value}'",
                            line_num, col, 1
                        ))
        else:
            newlines = value.count("\n")
            tokens.append(Token(kind, value, line_num, col))
            if newlines:
                line_num += newlines
                line_start = match.end() - (len(value) - value.rfind("\n") - 1)

    while bracket_stack:
        b, l, c = bracket_stack.pop()
        errors.append(SyntaxIssue(f"Unclosed bracket '{b}'", l, c, 1))

    return tokens, errors


SAMPLES = {
    "C": """// Clean C snippet
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int count = 5;
    float pi = 3.14159;
    char grade = 'A';
    while (count > 0) {
        count--;
    }
    printf("Result: %d\\n", factorial(5));
    return 0;
}
""",
    "C++": """// Clean C++ snippet
#include <iostream>
using namespace std;

class Shape {
public:
    virtual double area() = 0;
};

int main() {
    int total = 0;
    int values[] = {1, 2, 3, 4, 5};
    for (int i = 0; i < 5; i++) {
        total += values[i];
    }
    cout << "Total: " << total << endl;
    return 0;
}
""",
    "Java": """// Clean Java snippet
public class Calculator {
    public static int add(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
        int result = add(4, 7);
        boolean done = true;
        System.out.println("Result = " + result);
    }
}
""",
    "Python": '''# Clean Python snippet
def factorial(n):
    """Return n! recursively."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

count = 5
pi = 3.14159
items = [1, 2, 3, 4, 5]
while count > 0:
    count -= 1

print(f"Factorial of 5: {factorial(5)}")
''',
    "HTML": """<!-- Clean HTML snippet -->
<!DOCTYPE html>
<html>
  <head>
    <title>Demo Page</title>
  </head>
  <body class="main" id="top">
    <h1>Hello, world!</h1>
    <p>This is a <b>lexical analyzer</b> demo.</p>
    <input type="text" name="username" />
  </body>
</html>
""",
}


# ----------------------------------------------------------------------
# 2. THE GUI
# ----------------------------------------------------------------------

class LexicalAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lexical Analyzer & Syntax Validator")
        self.geometry("1380x860")
        self.minsize(1100, 600)

        self.theme = "light"
        self._debounce_id = None
        self._tree_token_map = {}
        self._symbol_token_map = {}
        self._error_token_map = {}

        self._build_style()
        self._build_layout()
        self.apply_theme()

        self.source_text.insert("1.0", SAMPLES["C"])
        self._refresh_line_numbers()
        self.run_tokenizer()

        # Enforce exact 50/50 division after initial paint
        self.after(50, self._set_50_50_split)

    def _build_style(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", rowheight=24, font=("Consolas", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9))
        self.style.configure("Panel.TLabel", font=("Segoe UI", 9))

    def _build_layout(self):
        # Centered Hero Header Card
        self.title_frame = tk.Frame(self, padx=20, pady=12, relief="flat")
        self.title_frame.pack(fill="x", padx=15, pady=(12, 10))

        self.title_label = tk.Label(
            self.title_frame,
            text="Lexical Analyzer",
            font=("Segoe UI", 16, "bold")
        )
        self.title_label.pack(anchor="center")

        self.subtitle_label = tk.Label(
            self.title_frame,
            text="Live tokenization, symbol tracking, and syntax validation. Click tokens or errors to jump directly to source.",
            font=("Segoe UI", 9)
        )
        self.subtitle_label.pack(anchor="center", pady=(3, 0))

        # Toolbar
        self.toolbar = tk.Frame(self)
        self.toolbar.pack(fill="x", padx=15, pady=(0, 8))

        self.lang_label = ttk.Label(self.toolbar, text="Language:", style="Sub.TLabel")
        self.lang_label.pack(side="left")

        self.language_var = tk.StringVar(value="C")
        self.lang_box = ttk.Combobox(
            self.toolbar,
            textvariable=self.language_var,
            values=list(LANGUAGES.keys()),
            state="readonly",
            width=8
        )
        self.lang_box.pack(side="left", padx=(6, 12))
        self.lang_box.bind("<<ComboboxSelected>>", lambda e: self.run_tokenizer())

        # Styled Action Buttons
        self.btn_tokenize = ttk.Button(
            self.toolbar, text="▶ Tokenize Now",
            style="Primary.TButton", command=self.run_tokenizer
        )
        self.btn_tokenize.pack(side="left", padx=(0, 6))

        self.btn_sample = ttk.Button(
            self.toolbar, text="Load Sample",
            style="Secondary.TButton", command=self.load_sample
        )
        self.btn_sample.pack(side="left", padx=(0, 6))

        self.btn_load = ttk.Button(
            self.toolbar, text="Load File...",
            style="Secondary.TButton", command=self.load_file
        )
        self.btn_load.pack(side="left", padx=(0, 6))

        self.btn_save = ttk.Button(
            self.toolbar, text="Save Tokens...",
            style="Accent.TButton", command=self.save_tokens
        )
        self.btn_save.pack(side="left", padx=(0, 6))

        self.btn_clear = ttk.Button(
            self.toolbar, text="Clear",
            style="Danger.TButton", command=self.clear_all
        )
        self.btn_clear.pack(side="left", padx=(0, 6))

        self.theme_button = ttk.Button(
            self.toolbar, text="🌙 Dark Mode",
            style="Toggle.TButton", command=self.toggle_theme
        )
        self.theme_button.pack(side="right", padx=(6, 0))

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(
            self.toolbar, textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"), bd=0
        )
        self.status_label.pack(side="right", padx=10)

        # Paned Window (Split view)
        self.main_pane = tk.PanedWindow(self, orient="horizontal", sashwidth=6, bd=0)
        self.main_pane.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # Left: Editor
        self.left_frame = tk.Frame(self.main_pane)
        self.editor_header_label = ttk.Label(self.left_frame, text="Source Code Editor (Live validation)", style="Sub.TLabel")
        self.editor_header_label.pack(anchor="w", pady=(0, 3))

        self.editor_frame = tk.Frame(self.left_frame)
        self.editor_frame.pack(fill="both", expand=True)

        self.line_numbers = tk.Text(
            self.editor_frame, width=4, padx=4, takefocus=0,
            border=0, state="disabled", font=("Consolas", 11)
        )
        self.line_numbers.pack(side="left", fill="y")

        self.source_text = tk.Text(
            self.editor_frame, wrap="none", undo=True,
            font=("Consolas", 11), padx=6, pady=6, border=0
        )
        self.source_text.pack(side="left", fill="both", expand=True)
        self.source_text.bind("<KeyRelease>", self._on_edit)

        # Right: Notebook + Summary
        self.right_frame = tk.Frame(self.main_pane)
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Tokens
        tokens_tab = tk.Frame(self.notebook)
        self.tree = ttk.Treeview(tokens_tab, columns=("no", "line", "type", "value"), show="headings", height=10)
        for col, label, width in (("no", "#", 45), ("line", "Line", 60), ("type", "Category", 130), ("value", "Value", 220)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        tree_vsb = ttk.Scrollbar(tokens_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=tree_vsb.set)
        tree_vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._jump_to(self.tree, self._tree_token_map))

        # Tab 2: Symbol Table
        symbols_tab = tk.Frame(self.notebook)
        self.symbol_tree = ttk.Treeview(symbols_tab, columns=("name", "line", "count"), show="headings", height=10)
        for col, label, width in (("name", "Name", 180), ("line", "First Line", 100), ("count", "Uses", 80)):
            self.symbol_tree.heading(col, text=label)
            self.symbol_tree.column(col, width=width, anchor="w")
        self.symbol_tree.pack(side="left", fill="both", expand=True)
        sym_vsb = ttk.Scrollbar(symbols_tab, orient="vertical", command=self.symbol_tree.yview)
        self.symbol_tree.configure(yscroll=sym_vsb.set)
        sym_vsb.pack(side="right", fill="y")
        self.symbol_tree.bind("<<TreeviewSelect>>", lambda e: self._jump_to(self.symbol_tree, self._symbol_token_map))

        # Tab 3: Syntax Errors
        errors_tab = tk.Frame(self.notebook)
        self.error_tree = ttk.Treeview(errors_tab, columns=("line", "col", "msg"), show="headings", height=10)
        for col, label, width in (("line", "Line", 60), ("col", "Col", 60), ("msg", "Syntax Issue", 300)):
            self.error_tree.heading(col, text=label)
            self.error_tree.column(col, width=width, anchor="w")
        self.error_tree.pack(side="left", fill="both", expand=True)
        err_vsb = ttk.Scrollbar(errors_tab, orient="vertical", command=self.error_tree.yview)
        self.error_tree.configure(yscroll=err_vsb.set)
        err_vsb.pack(side="right", fill="y")
        self.error_tree.bind("<<TreeviewSelect>>", lambda e: self._jump_to(self.error_tree, self._error_token_map))

        self.notebook.add(tokens_tab, text="Tokens")
        self.notebook.add(symbols_tab, text="Symbol Table")
        self.notebook.add(errors_tab, text="Syntax Errors (0)")

        # Summary Section
        self.bottom_frame = tk.Frame(self.right_frame, bd=1, relief="solid")
        self.bottom_frame.pack(fill="x", pady=(10, 0))

        self.summary_label = ttk.Label(self.bottom_frame, text="Summary & Metrics", style="Panel.TLabel")
        self.summary_label.pack(anchor="w", padx=10, pady=(6, 2))

        self.stats_container = tk.Frame(self.bottom_frame)
        self.stats_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.stats_text = tk.Text(
            self.stats_container,
            height=12,
            wrap="none",
            font=("Consolas", 10),
            bd=0,
            padx=8,
            pady=6,
            takefocus=0
        )
        self.stats_text.pack(side="left", fill="both", expand=True)

        self.stats_vsb = ttk.Scrollbar(self.stats_container, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscroll=self.stats_vsb.set)
        self.stats_vsb.pack(side="right", fill="y")

        # Add frames without unsupported weight arguments
        self.main_pane.add(self.left_frame, minsize=350)
        self.main_pane.add(self.right_frame, minsize=350)

    def _set_50_50_split(self):
        self.update_idletasks()
        total_width = self.main_pane.winfo_width()
        if total_width > 100:
            self.main_pane.sash_place(0, total_width // 2, 0)

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.apply_theme()

    def _configure_button_style(self, style_name, config, font):
        self.style.configure(
            style_name,
            font=font,
            background=config["bg"],
            foreground=config["fg"],
            borderwidth=0,
            focusthickness=0,
            padding=(10, 5)
        )
        self.style.map(
            style_name,
            background=[("active", config["active"]), ("pressed", config["active"])],
            foreground=[("active", config["fg"]), ("pressed", config["fg"])]
        )

    def apply_theme(self):
        p = THEMES[self.theme]
        colors = CATEGORY_COLORS[self.theme]
        btn_font = ("Segoe UI", 9, "bold")

        self.configure(bg=p["bg"])
        for frame in (self.toolbar, self.left_frame, self.right_frame, self.editor_frame, self.stats_container):
            frame.configure(bg=p["bg"])
        self.main_pane.configure(bg=p["bg"])

        # Styled Title Card
        self.title_frame.configure(bg=p["header_bg"], bd=1, relief="solid", highlightbackground=p["border"])
        self.title_label.configure(bg=p["header_bg"], fg=p["header_fg"])
        self.subtitle_label.configure(bg=p["header_bg"], fg=p["header_sub"])

        # TTK Button Styles
        self._configure_button_style("Primary.TButton", p["btn_primary"], btn_font)
        self._configure_button_style("Secondary.TButton", p["btn_secondary"], btn_font)
        self._configure_button_style("Accent.TButton", p["btn_accent"], btn_font)
        self._configure_button_style("Danger.TButton", p["btn_danger"], btn_font)
        self._configure_button_style("Toggle.TButton", p["btn_toggle"], btn_font)

        self.theme_button.configure(text="☀ Light Mode" if self.theme == "dark" else "🌙 Dark Mode")

        # Panels & Summary View
        self.bottom_frame.configure(bg=p["panel_bg"], highlightbackground=p["border"])
        self.stats_text.configure(bg=p["panel_bg"], fg=p["text_fg"], insertbackground=p["editor_insert"])
        self.status_label.configure(bg=p["bg"])

        # TTK Labels & Tabs
        self.style.configure("Sub.TLabel", background=p["bg"], foreground=p["sub_fg"])
        self.style.configure("Panel.TLabel", background=p["panel_bg"], foreground=p["sub_fg"])
        self.style.configure("Treeview", background=p["tree_bg"], fieldbackground=p["tree_bg"], foreground=p["tree_fg"])
        self.style.map("Treeview", background=[("selected", p["select_bg"])])
        self.style.configure("Treeview.Heading", background=p["panel_bg"], foreground=p["text_fg"])
        self.style.configure("TNotebook", background=p["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=p["panel_bg"], foreground=p["text_fg"])
        self.style.map("TNotebook.Tab", background=[("selected", p["bg"])])

        # Source Code Editor
        self.source_text.configure(bg=p["editor_bg"], fg=p["editor_fg"], insertbackground=p["editor_insert"])
        self.line_numbers.configure(bg=p["linenum_bg"], fg=p["linenum_fg"])

        for cat, color in colors.items():
            self.source_text.tag_configure(cat, foreground=color)
            self.tree.tag_configure(cat, foreground=color)

        self.source_text.tag_configure("ERROR", foreground=colors["ERROR"], background=p["error_bg"], underline=True)
        self.source_text.tag_configure("JUMP", background=p["jump_bg"])
        self.source_text.tag_raise("JUMP")
        self.source_text.tag_raise("sel")

    def _on_edit(self, event=None):
        self._refresh_line_numbers()
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self.run_tokenizer)

    def _refresh_line_numbers(self):
        line_count = int(self.source_text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state="disabled")

    def _jump_to(self, tree, mapping):
        selection = tree.selection()
        if not selection:
            return
        pos = mapping.get(selection[0])
        if not pos:
            return
        line, col, length = pos
        start = f"{line}.{col - 1}"
        end = f"{line}.{col - 1 + max(length, 1)}"
        self.source_text.tag_remove("JUMP", "1.0", "end")
        self.source_text.tag_add("JUMP", start, end)
        self.source_text.mark_set("insert", start)
        self.source_text.see(start)

    def clear_all(self):
        self.source_text.delete("1.0", "end")
        self.tree.delete(*self.tree.get_children())
        self.symbol_tree.delete(*self.symbol_tree.get_children())
        self.error_tree.delete(*self.error_tree.get_children())
        self._set_stats_content("")
        self.notebook.tab(2, text="Syntax Errors (0)")
        self.status_var.set("Cleared.")
        self.status_label.configure(fg=THEMES[self.theme]["sub_fg"])
        self._refresh_line_numbers()

    def load_sample(self):
        lang = self.language_var.get()
        self.source_text.delete("1.0", "end")
        self.source_text.insert("1.0", SAMPLES.get(lang, ""))
        self._refresh_line_numbers()
        self.run_tokenizer()

    def load_file(self):
        path = filedialog.askopenfilename(
            title="Open source file",
            filetypes=[("Source files", "*.c *.h *.cpp *.hpp *.java *.py *.html *.htm *.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            messagebox.showerror("Could not open file", str(exc))
            return

        ext_map = {".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++", ".java": "Java", ".py": "Python", ".html": "HTML"}
        for ext, lang in ext_map.items():
            if path.lower().endswith(ext):
                self.language_var.set(lang)
                break

        self.source_text.delete("1.0", "end")
        self.source_text.insert("1.0", content)
        self._refresh_line_numbers()
        
        errors = self.run_tokenizer()
        if errors:
            err_summary = "\n".join(f"• Line {e.line}, Col {e.col}: {e.message}" for e in errors[:5])
            if len(errors) > 5:
                err_summary += f"\n...and {len(errors) - 5} more issues."
            messagebox.showwarning(
                "Syntax Errors Encountered",
                f"File loaded with {len(errors)} error(s):\n\n{err_summary}"
            )

    def save_tokens(self):
        if not self.tree.get_children():
            messagebox.showinfo("Nothing to save", "Tokenize some code first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save token list", defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{'#':<5}{'Line':<7}{'Category':<16}{'Value'}\n")
            f.write("-" * 60 + "\n")
            for iid in self.tree.get_children():
                no, line, cat, val = self.tree.item(iid, "values")
                f.write(f"{no:<5}{line:<7}{cat:<16}{val}\n")
        self.status_var.set(f"Saved token list to {path}")

    def run_tokenizer(self):
        self._debounce_id = None
        language = self.language_var.get()
        source = self.source_text.get("1.0", "end-1c")

        # Clean tags & UI tables
        for cat in CATEGORY_LABELS:
            self.source_text.tag_remove(cat, "1.0", "end")
        self.source_text.tag_remove("JUMP", "1.0", "end")
        self.source_text.tag_remove("ERROR", "1.0", "end")
        self.tree.delete(*self.tree.get_children())
        self.symbol_tree.delete(*self.symbol_tree.get_children())
        self.error_tree.delete(*self.error_tree.get_children())
        self._tree_token_map.clear()
        self._symbol_token_map.clear()
        self._error_token_map.clear()

        tokens, syntax_errors = tokenize(source, language)
        symbol_cats = SYMBOL_CATEGORIES.get(language, {"IDENTIFIER"})
        symbols = {}
        counts = {}

        for i, tok in enumerate(tokens, start=1):
            counts[tok.category] = counts.get(tok.category, 0) + 1
            first_line_len = len(tok.value.splitlines()[0]) if tok.value else 0

            display_val = tok.value if len(tok.value) <= 40 else tok.value[:37] + "..."
            display_val = display_val.replace("\n", "\\n")
            iid = self.tree.insert(
                "", "end",
                values=(i, tok.line, CATEGORY_LABELS[tok.category], display_val),
                tags=(tok.category,))
            self._tree_token_map[iid] = (tok.line, tok.col, first_line_len)

            start_index = f"{tok.line}.{tok.col - 1}"
            end_index = f"{tok.line}.{tok.col - 1 + first_line_len}"
            try:
                self.source_text.tag_add(tok.category, start_index, end_index)
            except tk.TclError:
                pass

            if tok.category in symbol_cats:
                if tok.value not in symbols:
                    symbols[tok.value] = {"line": tok.line, "col": tok.col, "length": first_line_len, "count": 0}
                symbols[tok.value]["count"] += 1

        for name, info in symbols.items():
            iid = self.symbol_tree.insert("", "end", values=(name, info["line"], info["count"]))
            self._symbol_token_map[iid] = (info["line"], info["col"], info["length"])

        # Populate Syntax Errors & apply red highlighting
        for err in syntax_errors:
            eiid = self.error_tree.insert("", "end", values=(err.line, err.col, err.message))
            self._error_token_map[eiid] = (err.line, err.col, err.length)
            err_start = f"{err.line}.{err.col - 1}"
            err_end = f"{err.line}.{err.col - 1 + max(err.length, 1)}"
            try:
                self.source_text.tag_add("ERROR", err_start, err_end)
            except tk.TclError:
                pass

        total_issues = len(syntax_errors)
        self.notebook.tab(2, text=f"Syntax Errors ({total_issues})")
        self._update_stats(counts, len(tokens), total_issues)

        # Focus shift + Alert styling
        p = THEMES[self.theme]
        if total_issues > 0:
            self.status_var.set(f"⚠ {language}: {total_issues} syntax error(s) detected!")
            self.status_label.configure(fg=p["alert_fg"])
            self.notebook.select(2)
        else:
            self.status_var.set(f"✓ {language}: {len(tokens)} tokens, clean syntax.")
            self.status_label.configure(fg=p["ok_fg"])

        return syntax_errors

    def _set_stats_content(self, content):
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", content)
        self.stats_text.configure(state="disabled")

    def _update_stats(self, counts, total, error_count):
        if total == 0:
            self._set_stats_content("(no code yet)")
            return
        lines = []
        for cat, label in CATEGORY_LABELS.items():
            n = counts.get(cat, 0)
            if n:
                lines.append(f"{label:<22}: {n}")
        lines.append("-" * 34)
        lines.append(f"{'Total tokens':<22}: {total}")
        lines.append(f"{'Syntax errors':<22}: {error_count}")
        self._set_stats_content("\n".join(lines))


if __name__ == "__main__":
    app = LexicalAnalyzerApp()
    app.mainloop()

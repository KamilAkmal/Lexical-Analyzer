# Lexical Analyzer & Syntax Validator

A desktop GUI tool that tokenizes source code and highlights syntax errors — live as you type or when a file is loaded. Built entirely with Python's standard library (`tkinter` + `re`), so there are no external dependencies to install.


## Features

- **Multi-language support** — C, C++, Java, Python, and HTML
- **Live tokenization** — the editor re-analyzes your code automatically as you type (debounced), or on demand with a button click
- **Syntax error detection**, including:
  - Unclosed string/char literals
  - Unclosed multi-line comments
  - Unclosed or mismatched HTML tags
  - Mismatched brackets, parentheses, and braces
- **Color-coded token highlighting** directly in the source editor (keywords, identifiers, strings, numbers, operators, comments, errors, etc.)
- **Token table** — a full list of every token with its line, category, and value
- **Symbol table** — tracks identifiers/names and how many times each is used
- **Click-to-jump** — click any row in the Tokens, Symbol Table, or Syntax Errors tabs to jump straight to that location in the source editor
- **Summary & metrics panel** — per-category token counts, total tokens, and total errors
- **Load sample code** for any supported language, or load your own file from disk
- **Export** the generated token list to a `.txt` file
- **Light / Dark theme** toggle

## Screenshots

*(Add a screenshot or GIF of the app here, e.g. `docs/screenshot.png`)*

## Getting Started

### Prerequisites

- Python 3.7+
- `tkinter` (included with most standard Python installations; on some Linux distros install it separately, e.g. `sudo apt install python3-tk`)

No third-party packages are required.

### Running the app

```bash
python LexicalAnalyzer.py
```

## Usage

1. Choose a language from the **Language** dropdown (C, C++, Java, Python, or HTML).
2. Type or paste code into the editor, or use **Load Sample** / **Load File...** to get started quickly.
3. The tool tokenizes automatically as you type. Click **▶ Tokenize Now** to force a refresh.
4. Switch between the **Tokens**, **Symbol Table**, and **Syntax Errors** tabs on the right to inspect results.
5. Click any row in those tables to jump to the corresponding location in the source editor.
6. Use **Save Tokens...** to export the current token list to a text file.
7. Use **🌙 Dark Mode** / **☀ Light Mode** to toggle the theme.

## How it works

The analyzer uses regex-based token specifications for each supported language:

- C / C++ and Java share a similar tokenizer (comments, preprocessor directives, string/char literals, numbers, identifiers, operators, punctuation).
- Python has its own token spec that handles triple-quoted strings and Python-specific operators.
- HTML is parsed with a two-pass approach: an outer pass splits the source into tags, comments, doctype, and text; an inner pass parses each tag's attributes and detects unclosed tags/attributes and mismatched open/close tags using a tag stack.

Detected issues (unclosed strings, unclosed comments, unclosed/mismatched tags, mismatched brackets) are surfaced both inline in the editor (highlighted in red) and in the **Syntax Errors** tab with line/column information.

## Project structure

```
LexicalAnalyzer.py   # Single-file application: lexer engine + Tkinter GUI
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a pull request.

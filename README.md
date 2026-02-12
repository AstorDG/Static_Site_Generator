# Static Site Generator

A custom-built static site generator written in Python with zero external dependencies. This project transforms Markdown content from a folder of markdown files into production-ready static HTML files. It uses a hierarchical tree-based node architecture and recursive directory processing. It also handles static asset copying and can fit into different html templates. This project was implemented as part of the [Boot.dev](https://www.boot.dev/) programming course.

## Architecture

The architecture follows a three-layer HTML node hierarchy:

- **HTMLNode**: Abstract base class defining the interface for all HTML nodes
- **LeafNode**: Represents HTML elements with no children (text nodes, images, etc.)
- **ParentNode**: Represents HTML elements containing child nodes (containers like `<div>`, `<p>`, `<ul>`, etc.)

The transformation pipeline converts content through several stages:

```
Markdown → Blocks → TextNodes → HTMLNodes → HTML Tree → HTML String
```

## Program Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   content/      │────▶│  Recursive Dir   │────▶│  Markdown Files │
│   (source)      │     │   Traversal      │     │   Discovered    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Title Extract   │◀────│  Parse Markdown │
                        │  (from h1 tags)  │     │                 │
                        └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                                 ▼                        ▼
┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
│   Static/       │     │   template.html │      │  Generate HTML  │
│   (assets)      │     │   (HTML shell)  │      │   (Node Tree)   │
└────────┬────────┘     └────────┬────────┘      └────────┬────────┘
         │                       │                        │
         │                       ▼                        │
         │              ┌──────────────────┐              │
         └─────────────▶│   HTML Files     │◀─────────────┘
                        │   (Generated)    │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │      docs/       │
                        │    (output)      │
                        └──────────────────┘
```

### Execution Steps

1. **Static Asset Copying**: Recursively copies all files from `static/` to `docs/`
2. **Content Discovery**: Recursively traverses `content/` directory to find all `.md` files
3. **Page Generation**: For each Markdown file:
   - Parse Markdown into HTML node tree
   - Extract page title from h1 heading
   - Inject content and title into HTML template
   - Write generated HTML to the corresponding path in `docs/`

## The Markdown-to-HTML Pipeline

The parsing process occurs in distinct stages:

```
Raw Markdown
     │
     ▼
┌─────────────────────────┐
│  markdown_to_blocks()   │  → Split into block-level chunks
│   (Block detection)     │     (headings, lists, paragraphs, etc.)
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  text_to_textnodes()    │  → Parse inline formatting
│   (Inline parsing)      │     (bold, italic, code, links, images)
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  text_node_to_html_node │  → Convert to HTML representation
│   (Node conversion)     │     (TextNode → LeafNode/ParentNode)
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  Parent/Leaf Nodes      │  → Build HTML tree structure
│   (Tree assembly)       │     (Nest nodes into container elements)
└─────────────────────────┘
     │
     ▼
  HTML String (via to_html())
```


### Parsing
There are two levels of the markdown parsing pipeline.
#### Block level Parsing
Here the document is split into blocks of text which are defined by blank lines. Each block has its own type which represents the kind of text it is such as a heading or a code block.
#### Inline parsing
Once blocks are split up the inline text needs to be parsed to look for styling like bold or italic text and links or image links. 
This parsing step maps text lines to text nodes with their associated HTML type

#### Highlight: Custom Link/Image Parser
A key implementation detail is the `split_image_or_link_nodes()` function, which parses link and image syntax **without using regular expressions**.

##### Why parse manually
- **Simplicity**: Every parsing decision is explicit and modifiable.
- **Performance**: The regex parsing goes character by character as well to look for expressions. I would have had to do multiple regex fucntions to acheive the same funcionality. So I thought I would just look at the string once and get all of the necessary information.
- **Zero dependencies**: Uses only uses built in Python functionality.

##### The State Machine Approach

The parser maintains two boolean states:

- `in_link_text`: Currently parsing the text portion between `[` and `]`
- `in_link_url`: Currently parsing the URL portion between `(` and `)`

As it iterates through each character:

1. When `[` is encountered outside of any state → enter `in_link_text`
2. When `]` is encountered in `in_link_text` → capture text, enter `in_link_url`
3. When `)` is encountered in `in_link_url` → capture URL, create TextNode
4. For images, check if `[` is preceded by `!` to distinguish `![` from `[`

##### Example

Input: `Check out [my site](https://example.com) and ![logo](img.png)`

Process:
- Parse "Check out " as plain text
- Detect `[` → enter link text state, capture "my site"
- Detect `]` → exit link text, enter URL state
- Detect `)` → capture "https://example.com", create LINK_TEXT node
- Parse " and " as plain text
- Detect `![` → enter image state, capture "logo"
- Detect `]` → exit image text, enter URL state
- Detect `)` → capture "img.png", create IMAGE_TEXT node

## Key Components

### `node.py`

Contains the core data structures and parsing logic:

- **HTMLNode**: Base class with `tag`, `value`, `children`, and `props` attributes
- **LeafNode**: Renders as `<tag>value</tag>` or plain text
- **ParentNode**: Renders as `<tag>children_html</tag>` by concatenating child `to_html()` results
- **TextNode**: Intermediate representation with `text`, `text_type`, and optional `url`
- **Parsing functions**: Block detection, inline formatting, and conversion utilities

### `main.py`

Orchestrates the generation process:

- `copy_directory()`: Recursively copies static assets
- `generate_pages_recursive()`: Discovers and processes all Markdown files
- `generate_page()`: Converts a single Markdown file to HTML
- `main()`: Entry point with CLI argument handling for basepath

### `template.html`

HTML template containing placeholders:
- `{{ Title }}`: Replaced with extracted h1 heading
- `{{ Content }}`: Replaced with generated HTML from Markdown
This template is replacable or changeable so you could have different kinds of base sites to build off of.

## Usage

Generate the static site:

```bash
# Default basepath ("/")
python3 src/main.py

# Custom basepath (for GitHub Pages, etc.)
python3 src/main.py "/your-repo-name/"
```

The generator will:
1. Copy all files from `static/` to `docs/`
2. Process all `.md` files in `content/` and subdirectories
3. Output generated HTML to corresponding paths in `docs/`

## Project Structure

```
.
├── content/              # Markdown source files
│   ├── index.md
│   └── blog/
│       ├── tom/
│       ├── glorfindel/
│       └── majesty/
├── static/               # Static assets (CSS, images)
│   ├── index.css
│   └── images/
├── docs/                 # Generated output (created by generator)
├── src/
│   ├── main.py          # Entry point and orchestration
│   └── node.py          # Core classes and parsing logic
├── template.html         # HTML template
└── build.sh             # Build script
```

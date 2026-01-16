from typing import override
from enum import Enum

# =================== HTMLNode Section =========================


# A node of in an HTML tree. This can be either block level or inline Html
# tag: str : the html tag name
# value: str : the text inside this Html node
# children: list[HTMLNode] : The children of this Html node
# props: dict[str, str]: key-value pairs representing the attributes of the HTML tag of this node
class HTMLNode:
    def __init__(
        self,
        tag: str | None = None,
        value: str | None = None,
        children: list["HTMLNode"] | None = None,
        props: dict[str, str] | None = None,
    ):
        self.tag: str | None = tag
        self.value: str | None = value
        self.children: list[HTMLNode] | None = children
        self.props: dict[str, str] | None = props

    # This function is meant to be implemented by child classes
    def to_html(self) -> str:
        raise NotImplementedError

    # outputs a string representation of this node's attributes as a single line string where the {key} = {value}
    def props_to_html(self) -> str:
        result = ""
        if self.props is not None:
            for key in self.props.keys():
                result += f" {key}='{self.props[key]}'"
            return result
        else:
            return ""

    @override
    def __repr__(self) -> str:
        result = ""
        result += f"{self.tag}\n"
        result += f"{self.value}\n"
        result += f"{self.children}\n"
        result += f"{self.props}\n"
        return result


# An HTML node with no children
class LeafNode(HTMLNode):
    def __init__(
        self, tag: str | None, value: str | None, props: dict[str, str] | None = None
    ):
        super().__init__(tag, value, None, props)

    @override
    def to_html(self) -> str:
        if self.value is None:
            raise ValueError
        elif self.tag is None:
            return self.value
        else:
            result = f"<{self.tag}{self.props_to_html()}>{self.value}</{self.tag}>"
            return result

    @override
    def __repr__(self):
        return f"LeafNode({self.tag}, {self.value}, {self.props})"


# an HTML node that must have children
class ParentNode(HTMLNode):
    def __init__(
        self,
        tag: str | None,
        children: list[HTMLNode] | None,
        props: dict[str, str] | None = None,
    ):
        super().__init__(tag, None, children, props)

    # The main point of this class is this function. It formats all of the children's html into this parent node's
    @override
    def to_html(self) -> str:
        if self.tag is None:
            raise ValueError("No tag")
        elif self.children is None:
            raise ValueError("No children")
        else:
            result = f"<{self.tag}{self.props_to_html()}>"
            for child in self.children:
                result += child.to_html()
            return result + f"</{self.tag}>"


# ================ TextNode Section ======================


class TextType(Enum):
    TEXT = "text"
    BOLD_TEXT = "bold"
    ITALIC_TEXT = "italic"
    CODE_TEXT = "code"
    LINK_TEXT = "link"
    IMAGE_TEXT = "image"


# An intermediate node containing some inline text with its text type. If it's a link or image store it's url link
class TextNode:
    def __init__(self, text: str, text_type: TextType, url: str | None = None):
        self.text: str = text
        self.text_type: TextType = text_type
        self.url: str | None = url

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, TextNode):
            return (
                self.text == other.text
                and self.text_type == other.text_type
                and self.url == other.url
            )
        return False

    @override
    def __repr__(self):
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"


# =============== Block_type ===================
class Block_Type(Enum):
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    ULIST = "unordered_list"
    OLIST = "ordered_list"
    PARAGRAPH = "paragraph"


# ================== Text_Node Helper functions ===================


# Returns a LeafNode based on the text type with the appropriate HTML tag. If it's a link or image save the link in the leaf node.
def text_node_to_html_node(text_node: TextNode) -> LeafNode:
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text, None)
    elif text_node.text_type == TextType.BOLD_TEXT:
        return LeafNode("b", text_node.text, None)
    elif text_node.text_type == TextType.ITALIC_TEXT:
        return LeafNode("i", text_node.text, None)
    elif text_node.text_type == TextType.CODE_TEXT:
        return LeafNode("code", text_node.text, None)
    elif text_node.text_type == TextType.LINK_TEXT:
        return LeafNode("a", text_node.text, {"href": text_node.url})
    elif text_node.text_type == TextType.IMAGE_TEXT:
        return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})
    else:
        raise ValueError(f"invalid text type: {text_node.text_type}")


# Takes a list of TextNodes and returns a new list that parses out the given text type on the given delimiter.
# It keeps the text in order.
def split_nodes_delimiter(
    old_nodes: list[TextNode], delimiter: str, text_type: TextType
) -> list[TextNode]:
    resulting_nodes: list[TextNode] = []

    for node in old_nodes:
        if node.text_type is TextType.TEXT:
            new_nodes: list[TextNode] = []
            split_text = node.text.split(delimiter)
            if len(split_text) % 2 == 0:
                raise ValueError("invalid markdown, formatted section not closed")
            for i in range(len(split_text)):
                if split_text[i] == "":
                    continue
                if i % 2 == 0:
                    new_nodes.append(TextNode(split_text[i], TextType.TEXT))
                else:
                    new_nodes.append(TextNode(split_text[i], text_type))

            resulting_nodes.extend(new_nodes)
        else:
            resulting_nodes.append(node)
    return resulting_nodes


# Extracts links and images out of plain text nodes and returns a new list of of TextNodes
# Preserves the order of the text.
def split_image_or_link_nodes(
    old_nodes: list[TextNode], text_type: TextType
) -> list[TextNode]:
    new_nodes: list[TextNode] = []
    start_delimiter = "["
    for node in old_nodes:
        current_nodes: list[TextNode] = []
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        text_index = 0
        start_index = 0
        in_link_text = False
        in_link_url = False
        current_link_text = ""
        while text_index < len(node.text):
            if in_link_text:
                if node.text[text_index] == "]":
                    current_link_text = node.text[start_index:text_index]
                    in_link_text = False
                    in_link_url = True
                    start_index = text_index + 2
                    text_index += 3
                else:
                    text_index += 1
            elif in_link_url:
                if node.text[text_index] == ")":
                    current_nodes.append(
                        TextNode(
                            current_link_text,
                            text_type,
                            node.text[start_index:text_index],
                        )
                    )
                    in_link_url = False
                    start_index = text_index + 1
                    text_index += 1
                else:
                    text_index += 1
            else:
                if (
                    node.text[text_index] == start_delimiter
                    and text_type == TextType.LINK_TEXT
                ):
                    if start_index != text_index:
                        current_nodes.append(
                            TextNode(node.text[start_index:text_index], TextType.TEXT)
                        )
                    in_link_text = True
                    start_index = text_index + 1
                    text_index += 2
                elif (
                    node.text[text_index] == start_delimiter
                    and text_type == TextType.IMAGE_TEXT
                ):
                    if node.text[text_index - 1] == "!":
                        if text_index - start_index > 1:
                            current_nodes.append(
                                TextNode(
                                    node.text[start_index : text_index - 1],
                                    TextType.TEXT,
                                )
                            )
                        in_link_text = True
                        start_index = text_index + 1
                        text_index += 2
                    else:
                        text_index += 1
                else:
                    text_index += 1
        if text_index - start_index > 0:
            current_nodes.append(
                TextNode(node.text[start_index:text_index], TextType.TEXT)
            )
        if in_link_text or in_link_url:
            print(node)
            raise ValueError("invalid markdown")
        new_nodes.extend(current_nodes)

    return new_nodes


# This function combines the two splitting methods to take some raw markdown text and convert it into a list of
# textnodes with the appropriate text type.
def text_to_textnodes(text: str) -> list[TextNode]:
    text_nodes: list[TextNode] = [TextNode(text, TextType.TEXT)]
    text_nodes = split_nodes_delimiter(text_nodes, "**", TextType.BOLD_TEXT)
    text_nodes = split_nodes_delimiter(text_nodes, "_", TextType.ITALIC_TEXT)
    text_nodes = split_nodes_delimiter(text_nodes, "`", TextType.CODE_TEXT)
    text_nodes = split_image_or_link_nodes(text_nodes, TextType.IMAGE_TEXT)
    text_nodes = split_image_or_link_nodes(text_nodes, TextType.LINK_TEXT)
    return text_nodes


# ================= Block Helper Functions =======================
# Takes a single block of markdown and returns the type of that block based on its properties.
def block_to_block_type(markdown_block: str) -> Block_Type:
    blocks = markdown_block.split("\n")
    if markdown_block.startswith(("# ", "## ", "### ", "#### ", "##### ", "###### ")):
        return Block_Type.HEADING
    if len(blocks) > 1 and blocks[0].startswith("```") and blocks[-1].startswith("```"):
        return Block_Type.CODE
    if markdown_block.startswith(">"):
        for line in blocks:
            if not line.startswith(">"):
                return Block_Type.PARAGRAPH
        return Block_Type.QUOTE
    if markdown_block.startswith("- "):
        for line in blocks:
            if not line.startswith("- "):
                return Block_Type.PARAGRAPH
        return Block_Type.ULIST
    if markdown_block.startswith("1. "):
        i = 1
        for line in blocks:
            if not line.startswith(f"{i}. "):
                return Block_Type.PARAGRAPH
            i += 1
        return Block_Type.OLIST
    return Block_Type.PARAGRAPH


# Take a string representing a full markdown document and splits it into a list of strings seperated by a blank line.
def markdown_to_blocks(markdown: str) -> list[str]:
    blocks = markdown.split("\n\n")
    filtered_blocks: list[str] = []
    for block in blocks:
        if block == "":
            continue
        else:
            filtered_blocks.append(block.strip())
    return filtered_blocks


# converts a markdown document into a Tree of HTMLNodes.
def markdown_to_html_node(markdown: str) -> HTMLNode:
    markdown_blocks = markdown_to_blocks(markdown)
    block_nodes: list[HTMLNode] = []
    for block in markdown_blocks:
        current_block_type = block_to_block_type((block))

        if current_block_type == Block_Type.HEADING:
            heading_count = 0
            for char in block:
                if char == "#":
                    heading_count += 1
                else:
                    break
            if heading_count > 6:
                raise ValueError("Too many pound symbols for a heading")
            heading_node = ParentNode(f"h{heading_count}", None)
            text_nodes = text_to_textnodes(block[heading_count + 1 :])
            child_nodes: list[HTMLNode] = []
            for node in text_nodes:
                child_nodes.append(text_node_to_html_node(node))
            heading_node.children = child_nodes
            block_nodes.append(heading_node)

        elif current_block_type == Block_Type.CODE:
            code_text = block[4:-3]
            text_node = TextNode(code_text, TextType.TEXT)
            child_node = text_node_to_html_node(text_node)
            code_node = ParentNode("code", [child_node])
            wrapped_code_node = ParentNode("pre", [code_node])
            block_nodes.append(wrapped_code_node)

        elif current_block_type == Block_Type.QUOTE:
            lines: list[str] = block.split("\n")
            quote_text_lines: list[str] = []
            for line in lines:
                quote_text_lines.append(line[2:])
            quote_text = " ".join(quote_text_lines)
            quote_text_nodes = text_to_textnodes(quote_text)
            quote_child_nodes: list[HTMLNode] = []
            for node in quote_text_nodes:
                quote_child_nodes.append(text_node_to_html_node(node))
            quote_parent_node = ParentNode("blockquote", quote_child_nodes)
            block_nodes.append(quote_parent_node)

        elif current_block_type == Block_Type.OLIST:
            list_lines = block.split("\n")
            list_items: list[HTMLNode] = []
            for list_line in list_lines:
                line_text = list_line.split(". ", 1)
                line_text_nodes = text_to_textnodes(line_text[1])
                line_child_nodes: list[HTMLNode] = []
                for line_text_node in line_text_nodes:
                    line_child_nodes.append(text_node_to_html_node(line_text_node))
                list_items.append(ParentNode("li", line_child_nodes))
            block_nodes.append(ParentNode("ol", list_items))

        elif current_block_type == Block_Type.ULIST:
            list_lines = block.split("\n")
            list_items: list[HTMLNode] = []
            for list_line in list_lines:
                line_text = list_line[2:]
                line_text_nodes = text_to_textnodes(line_text)
                line_child_nodes: list[HTMLNode] = []
                for line_text_node in line_text_nodes:
                    line_child_nodes.append(text_node_to_html_node(line_text_node))
                list_items.append(ParentNode("li", line_child_nodes))
            block_nodes.append(ParentNode("ul", list_items))

        elif current_block_type == Block_Type.PARAGRAPH:
            lines = block.split("\n")
            paragraph_text = " ".join(lines)
            paragraph_text_nodes = text_to_textnodes(paragraph_text)
            paragraph_child_nodes: list[HTMLNode] = []
            for node in paragraph_text_nodes:
                paragraph_child_nodes.append(text_node_to_html_node(node))
            paragraph_node = ParentNode("p", paragraph_child_nodes)
            block_nodes.append(paragraph_node)

    return ParentNode("div", block_nodes, None)


# Extracts the title of a markdown string and returns it as a string object
def extract_title(markdown_content: str) -> str:
    markdown_lines = markdown_content.split("\n")
    for line in markdown_lines:
        if line.startswith("# "):
            title = line.strip("# ")
            return title
    raise Exception("No Title")

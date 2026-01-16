import os
import shutil
import sys
from node import markdown_to_html_node, extract_title


def generate_page(
    from_path: str, template_path: str, dest_path: str, basepath: str
) -> None:
    if not os.path.exists(from_path):
        raise ValueError("No file at that location")
    if not os.path.exists(template_path):
        raise ValueError("No template at that location")
    print(f"Generating page {from_path} to {dest_path} using {template_path}")
    with open(from_path) as m_file:
        markdown_file = m_file.read()
    with open(template_path) as html_template:
        template_file = html_template.read()
    html_tree = markdown_to_html_node(markdown_file)
    html_string = html_tree.to_html()
    title = extract_title(markdown_file)
    new_title = template_file.replace("{{ Title }}", title)
    new_content = new_title.replace("{{ Content }}", html_string)
    new_content = new_content.replace('href="/', f'href="{basepath}')
    new_content = new_content.replace('src="/', f'href="{basepath}')
    with open(dest_path, "w") as output:
        _ = output.write(new_content)

    return None


def generate_pages_recursive(
    dir_path_content: str, template_path: str, dest_dir_path: str, basepath: str
) -> None:
    if not os.path.exists(dir_path_content):
        raise ValueError("No Content on this path")
    try:
        os.mkdir(dest_dir_path)
    except FileExistsError:
        pass
    dir_content = os.listdir(dir_path_content)
    for content in dir_content:
        content_path = os.path.join(dir_path_content, content)
        if os.path.isfile(content_path):
            if content_path[-3:] == ".md":
                generate_page(
                    content_path,
                    template_path,
                    f"{os.path.join(dest_dir_path, content[:-3])}.html",
                    basepath,
                )
            else:
                continue
        else:
            generate_pages_recursive(
                f"{content_path}/",
                template_path,
                f"{os.path.join(dest_dir_path, content)}",
                basepath,
            )

    return None


# Recurisvely copys all of the files from one directory into another.
def copy_directory(origin: str, destiniation: str) -> None:
    if not os.path.exists(origin):
        raise ValueError("Origin does not exist")
    # delete contents of a destiniation if it already exists for a clean copy
    if os.path.exists(destiniation):
        shutil.rmtree(destiniation)
    os.mkdir(destiniation)
    origin_contents = os.listdir(origin)
    for content in origin_contents:
        content_path = os.path.join(origin, content)
        if os.path.isfile(content_path):
            _ = shutil.copy(content_path, destiniation)
        else:
            copy_directory(
                f"{content_path}/", f"{os.path.join(destiniation, content)}/"
            )


def main():
    if len(sys.argv) == 0:
        base_path = "/"
    else:
        base_path = sys.argv[0]
    copy_directory(
        "./static/",
        "./docs/",
    )
    generate_pages_recursive("./content/", "./template.html", "./docs/", base_path)


main()

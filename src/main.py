import os
import shutil
import sys
from node import markdown_to_html_node, extract_title


# The base case for the generate_pages_recursive function.
# Get the html from the markdown file. Fills in the template with the html and the title.
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
    filled_in_template = template_file.replace("{{ Title }}", title)
    filled_in_template = filled_in_template.replace("{{ Content }}", html_string)
    filled_in_template = filled_in_template.replace('href="/', f'href="{basepath}')
    filled_in_template = filled_in_template.replace('src="/', f'src="{basepath}')
    with open(dest_path, "w") as output:
        _ = output.write(filled_in_template)

    return None


# Generates HTML files in the given destination directory from the markdown files in the content directory.
# The function searches through directories and if a markdown file is found it creates a new page.
# If a directory is found it'll search through that directory as well.
# If another file type is found it is ignored.
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


# Gets the basepath from the command line and sets a default if there isn't one.
# Copys the static content into the docs directory.
# Generates html files from the content directory using the given html template into the docs directory
def main():
    if len(sys.argv) < 1:
        base_path = "/"
    else:
        base_path = sys.argv[1]
    copy_directory(
        "./static/",
        "./docs/",
    )
    generate_pages_recursive("./content/", "./template.html", "./docs/", base_path)


# Calls the main function
main()

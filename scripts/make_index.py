import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def get_source_folder():
    "Get a path to the folder that github pages publishes from."
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True)
    repo_root = proc.stdout.decode("utf-8").strip()
    repo_root = Path(repo_root)
    source_folder = repo_root / "docs"

    return source_folder


def get_display_name(file):
    return file.stem.replace("_", " ")


def main():
    env = Environment(loader=FileSystemLoader("templates/"))
    index_template = env.get_template("index.jinja")

    source_folder = get_source_folder()

    files = [file for file in source_folder.iterdir() if file.name != "index.html"]
    files.sort()

    rendered = index_template.render(files=[(file.name, get_display_name(file)) for file in files])
    with open(source_folder / "index.html", "w") as f:
        f.write(rendered)


if __name__ == "__main__":
    main()

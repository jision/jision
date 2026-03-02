from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def render_readme(context, template_dir=None, template_name="README.md.j2"):
    """Load Jinja2 template and render with context."""
    if template_dir is None:
        template_dir = str(Path(__file__).resolve().parent.parent / "templates")

    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**context)


def write_readme(content, output_path=None):
    """Write rendered content to README.md at the repo root."""
    if output_path is None:
        output_path = str(Path(__file__).resolve().parent.parent / "README.md")

    Path(output_path).write_text(content, encoding="utf-8")

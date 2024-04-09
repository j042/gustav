# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import gustaf

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "gustaf"
copyright = "2022, Jaewook Lee"  # noqa A001
author = "Jaewook Lee"
release = gustaf.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_mdinclude",
]


templates_path = ["_templates"]
exclude_patterns = []

pygments_style = "sphinx"


# autodoc options
autodoc_mock_imports = [
    "numpy",
    "splinepy",
    "vedo",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# html_theme = "piccolo_theme"
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "logo": {
        "image_light": "_static/gus_light_mode.png",
        "image_dark": "_static/gus_dark_mode.png",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/tataratat/gustaf",
            "icon": "fa-brands fa-square-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/gustaf/",
            "icon": "fa-solid fa-box",
        },
    ],
}
html_favicon = "_static/favicon.ico"

html_static_path = ["_static"]
html_css_files = ["style.css"]

autodoc_default_options = {
    "autosummary": True,
}

autosummary_context = {
    "skipmethods": ["__init__"],
}

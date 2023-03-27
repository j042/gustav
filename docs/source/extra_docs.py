"""
A script for extra doc generation.
Feel free to extend!

Contents:
1. Create markdown table of show options.
"""
import pathlib

import gustaf as gus

if __name__ == "__main__":
    here = pathlib.Path(__file__).parent.resolve()
    # create md dir
    (here / "../md").resolve().mkdir(parents=True, exist_ok=True)

    # 1. Show options.
    with open((here / "../md/show_options.md").resolve(), "w") as f:
        derived = gus.helpers.options.ShowOption.__subclasses__()
        for cls in derived:
            f.write(f"## {cls.__qualname__}\n\n")
            for backend, options in cls._valid_options.items():
                f.write(f"### {backend}\n\n")
                for option in options.values():
                    t_str = str(option.allowed_types)
                    t_str = (
                        t_str.replace("<class", "")
                        .replace("'", "")
                        .replace(">", "")
                    )
                    f.write(
                        f"<details><summary><strong>{option.key}"
                        "</strong></summary><p>\n"
                    )
                    f.write(f"\n{option.description}  \n")
                    f.write(f"- _allowed types_: {t_str}  \n")
                    f.write("</p></details> \n\n")

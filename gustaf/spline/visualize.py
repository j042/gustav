"""gustaf/spline/visualize.py.

Spline visualization module. Supports visualization of following spline
(para_dim, dim) pairs: ((1, 2), (1, 3), (2, 2), (2, 3), (3, 3)
"""
import numpy as np

from gustaf import Vertices, settings
from gustaf.helpers import options
from gustaf.utils.arr import enforce_len


class SplineShowOption(options.ShowOption):
    """
    Show options for splines.
    """

    __slots__ = ()

    # if we start to support more backends, most of this options should become
    # some sort of spline common.
    _valid_options = options.make_valid_options(
        *options.vedo_common_options,
        options.Option(
            "vedo",
            "control_points",
            "Show spline's control points and control mesh.",
            (bool,),
        ),
        options.Option("vedo", "knots", "Show spline's knots.", (bool,)),
        options.Option(
            "vedo",
            "fitting_queries",
            "Shows fitting queries if they are locally saved in splines.",
            (bool,),
        ),
        options.Option(
            "vedo",
            "control_points_alpha",
            "Transparency of control points in range [0, 1].",
            (float, int),
        ),
        options.Option(
            "vedo",
            "control_point_ids",
            "Show ids of control_points.",
            (bool,),
        ),
        options.Option(
            "vedo",
            "resolutions",
            "Sampling resolution for spline.",
            (int, list, tuple, np.ndarray),
        ),
    )

    _helps = "GustafSpline"

    def __init__(self, helpee):
        """
        Parameters
        ----------
        helpee: GustafSpline
        """
        self._helpee = helpee
        # checks if helpee inherits from GustafSpline
        if self._helps not in str(type(helpee).__mro__):
            raise TypeError(
                f"This show option if for {self._helps}.",
                f"Given helpee is {type(helpee)}.",
            )
        self._options = dict()
        self._backend = settings.VISUALIZATION_BACKEND
        self._options[self._backend] = dict()


def _vedo_showable(spline):
    """
    Goes through common precedures for preparing showable splines.

    Parameters
    ----------
    None

    Returns
    -------
    gus_dict: dict
      dict of sampled spline as gustaf objects
    """
    # get spline and knots
    gus_primitives = eval(f"_vedo_showable_para_dim_{spline.para_dim}(spline)")

    # apply spline color
    sampled_spline = gus_primitives
    default_color = "green" if spline.para_dim > 1 else "black"
    sampled_spline.show_options["c"] = spline.show_options.get(
        "c", default_color
    )
    sampled_spline.show_options["alpha"] = spline.show_options.get(
        "alpha", None
    )
    sampled_spline.show_options["lighting"] = spline.show_options.get(
        "lighting", "glossy"
    )
    # cmap
    # cmapalpha
    # vmin
    # vmax
    # scalarbar
    # arrowdata
    # arrowdata_scale
    # arrowdata_color

    # double check on same obj ref
    gus_primitives["spline"] = gus_primitives

    # control_points & control_points_alpha
    if spline.show_options.get("control_points", True):
        # pure control mesh
        cmesh = spline.extract.control_mesh()  # either edges or faces
        if spline.para_dim != 1:
            cmesh = cmesh.toedges(unique=True)

        cmesh.show_options["c"] = "red"
        cmesh.show_options["lw"] = 4
        cmesh.show_options["alpha"] = spline.show_options.get(
            "control_points_alpha", 0.8
        )
        # add
        gus_primitives["control_mesh"] = cmesh

        # control points (vertices)
        cps = spline.extract.control_points()
        cps.show_options["c"] = "red"
        cps.show_options["r"] = 10
        cps.show_options["alpha"] = spline.show_options.get(
            "control_points_alpha", 0.8
        )
        # add
        gus_primitives["control_points"] = cps

        if spline.show_options.get("control_point_ids", True):
            # a bit redundant, but nicely separable
            cp_ids = spline.extract.control_points()
            cp_ids.show_options["labels"] = np.arange(cp_ids)
            cp_ids.show_options["label_options"] = {"font": "VTK"}
            gus_primitives["control_point_ids"] = cp_ids

    # fitting queries
    if hasattr(spline, "_fitting_queries") and spline.show_options.get(
        "fitting_queries", True
    ):
        fqs = Vertices(spline._fitting_queries)
        fqs.show_options["c"] = "blue"
        fqs.show_options["r"] = 10
        gus_primitives["fitting_queries"] = fqs

    return gus_primitives


def _vedo_showable_para_dim_1(spline):
    """
    Assumes showability check has been already performed

    Parameters
    ----------
    spline: GustafSpline

    Returns
    -------
    gus_primitives: dict
      keys are {spline, knots}
    """
    gus_primitives = dict()
    res = enforce_len(
        spline.show_options.get("resolutions", 100), spline.para_dim
    )
    sp = spline.extract.edges(res[0])

    # specify curve width
    sp.show_options["lw"] = 8
    # add spline
    gus_primitives["spline"] = sp

    # place knots
    if spline.show_options.get("knots", True):
        uks = np.asanyarray(spline.unique_knots[0]).reshape(-1, 1)
        knots = Vertices(spline.evaluate(uks))
        knots.show_options["labels"] = ["x"] * len(uks)
        knots.show_options["label_options"] = {
            "justify": "center",
            "c": "green",
        }
        gus_primitives["knots"] = knots

    return gus_primitives


def _vedo_showable_para_dim_2(spline):
    """
    Assumes showability check has been already performed

    Parameters
    ----------
    spline: GustafSpline

    Returns
    -------
    gus_primitives: dict
      keys are {spline, knots}
    """
    gus_primitives = dict()
    res = enforce_len(
        spline.show_options.get("resolutions", 100), spline.para_dim
    )
    sp = spline.extract.faces(res)
    gus_primitives["spline"] = sp

    # knots
    if spline.show_options.get("knots", True):
        knot_lines = spline.extract.edges(res, all_knots=True)
        knot_lines.show_options["c"] = "black"
        knot_lines.show_options["lw"] = 3
        gus_primitives["knots"] = knot_lines


def _vedo_showable_para_dim_3(spline):
    """
    Currently same as _vedo_showable_para_dim_2
    """
    return _vedo_showable_para_dim_2(spline)

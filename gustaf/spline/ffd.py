"""
gustaf/gustaf/ffd.py

Freeform Deformation!


Adaptation of previous implementation in internal python package gustav by
Jaewook Lee.
"""
from typing import Any, List, Optional, Union
import numpy as np
from gustaf._base import GustafBase
from gustaf.faces import Faces
from gustaf.show import show_vedo
from gustaf._typing import SPLINE_TYPES, MESH_TYPES
from gustaf.create.spline import with_bounds
from gustaf import settings


class FFD (GustafBase):

    def __init__(
        self,
        mesh: Optional[MESH_TYPES] = None,
        spline: Optional[SPLINE_TYPES] = None
    ):
        """
        Free-form deformation is a method used to deform an object by a
        deformation function. In our case the object is given via a mesh, the
        currently supported mesh-types are given by the variable
        :py:const:`gustaf._typing.MESH_TYPES`, and the deformations function
        by a spline, supported splines are given by the variable
        :py:const.:`gustaf._typing.SPLINE_TYPES`. The splines parametric
        dimension will be scaled in to a unit-hypercube as well as the
        original meshes vertices. The outline of the resulting mesh is given
        by the physical space of the spline.

        The FFD class provides functions to modify the spline by completely
        overwriting the spline whole spline or parts of it. To obtain the
        deformed mesh mapped into the latest spline, retrieve the mesh
        attribute.

        Please not that even though an object of the class can be initiated
        without a mesh, it is not possible to compute the deformation without
        one. Please ensure that at least a mesh is defined before retrieving
        the (deformed) mesh. If only a mesh is provided a default spline where
        the geometric dimensions have the bounds of the mesh is defined.

        A previously available partial FFD is currently not implemented, and
        is planned to be implemented in a separate class (LocalFFD).

        Parameters
        ----------
        mesh: Optional[MESH_TYPES]
            Mesh used in the FFD. Defaults to None.
        spline: Optional[SPLINE_TYPES]
            Spline used in the FFD. Defaults to None.

        Class Attributes
        ----------------
        _spline: SPLINE_TYPES
            Internal current spline
        _mesh: MESH_TYPES
            unscaled base mesh
        _q_vertices: np.ndarray (n, dim)
            Scaled vertices of the base mesh
        _is_calculated: bool
            Attribute tracking if changes are present since last calculation
        _is_calculated_trackable: bool
            Getter for cp was called. Cps can be changed without knowledge
            need to recalculate every time.
        _orig_para_dim_ranges: np.ndarray:
            Original spline parametric dimension boundaries, used in
            knot_insertion to scale the knots to be inserted into the same
            scale as the internal spline (which has a hypercubic parametric
            dimensional space)

        Returns
        -------
        None
        """
        # Use property definitions to store the values
        self._spline: SPLINE_TYPES = None
        self._mesh: MESH_TYPES = None
        self._q_vertices: np.ndarray = None
        self._is_calculated: bool = False
        self._is_calculated_trackable: bool = True
        self._orig_para_dim_ranges: np.ndarray = None

        if spline is not None:
            self.spline = spline
        if mesh is not None:
            self.mesh = mesh

        self._is_calculated = False

    @property
    def mesh(self,) -> MESH_TYPES:
        """Returns copy of current mesh. Before copying, it applies
        deformation.

        Returns
        -------
        MESH_TYPES
            Current Mesh with the deformation according to the current spline.
        """
        self._deform()
        return self._mesh.copy()

    @mesh.setter
    def mesh(self, mesh: MESH_TYPES):
        """
        Sets mesh. If it is first time, the copy of it will be saved as
        original mesh. If spline is already defined and in transformed status,
        it applies transformation directly.

        Parameters
        -----------
        mesh: MESH_TYPES
            Mesh used for the FFD

        Returns
        --------
        None
        """
        if self._spline is None:
            # Define a default spline if mesh is given but no spline
            par_dim = mesh.vertices.shape[1]
            self.spline = with_bounds(
                [[0]*par_dim, [1]*par_dim],
                mesh.get_bounds())

        self._logi("Setting mesh.")
        self._logi("Mesh Info:")
        self._logi(
            "  Vertices: {v}.".format(v=mesh.vertices.shape)
        )
        self._logi(
            "  Bounds: {b}.".format(b=mesh.get_bounds())
        )
        self._mesh = mesh.copy()  # copy to make sure given mesh stay untouched

        # Checks dimensions and ranges critical for a correct FFD calculation
        if not self._spline.para_dim == self._spline.dim:
            self._logw("The parametric and geometric dimensions of the "
                       "spline are not the same.")
        if not self._spline.dim == self._mesh.vertices.shape[1]:
            self._logw("The geometric dimensions of the spline and the "
                       "dimension of the mesh are not the same.")

        self._scale_mesh_vertices()
        self._is_calculated = False
        # trackable true since cp overwritten since last getter call
        self._is_calculated_trackable = True

    @property
    def spline(self):
        """
        Returns a copy of the spline. Please use the setter to explicitly make
        changes to the spline.

        Parameters
        -----------
        None

        Returns
        --------
        self._spline: Spline
        """
        self._logd("Returning copy of current spline.")
        return self._spline.copy() if self._spline is not None else None

    @spline.setter
    def spline(self, spline: SPLINE_TYPES):
        """
        Sets spline. The spline parametric range bounds will be converted
        into the bounds [0,1]^para_dim.

        Parameters
        -----------
        spline: SPLINE_TYPES
            New Spline for the next deformation

        Returns
        --------
        None
        """
        self._spline = spline.copy()
        if "knot_vectors" in spline.required_properties:
            self._orig_para_dim_ranges = spline.parametric_bounds.T
            self._spline.normalize_knot_vectors()
        else:
            self._orig_para_dim_ranges = [[0, 1]]*spline.para_dim

        self._logi("Setting Spline.")
        self._logi("Spline Info:")
        self._logi(
            f"  Parametric dimensions: {spline.para_dim}."
        )
        self._is_calculated = False

    def _scale_mesh_vertices(self):
        """
        Scales the mesh vertices into the dimension of a hypercube and save
        them in self._q_vertices.
        """
        self._logd("Fitting mesh into spline's parametric space.")

        self._q_vertices = self._mesh.vertices.copy()

        original_mesh_bounds = self._mesh.get_bounds()

        # save mesh offset and scale for reasons
        self._mesh_offset = original_mesh_bounds[0]
        self._mesh_scale = 1/(original_mesh_bounds[1] -
                              original_mesh_bounds[0])

        # scale and offset vertices coordinates
        self._q_vertices -= self._mesh_offset
        self._q_vertices *= self._mesh_scale

        self._logd("Successfully scaled and transformed mesh vertices!")

    def _deform(self):
        """
        Deforms mesh if spline or mesh changes were detected since last
        calculation. Meant for internal use.

        Parameters
        -----------
        None

        Returns
        --------
        None
        """
        if self._mesh is None or self._spline is None:
            raise RuntimeError(
                "Can not perform deformation for the FFD, since either the "
                "spline and/or the mesh are not yet defined. Please define "
                "both a spline and mesh before deforming the mesh.")
        if self._is_calculated and self._is_calculated_trackable:
            return None

        self._logd("Applying FFD: Transforming vertices")

        # Here, we take _q_vertices, due to possible scale/offset.
        self._mesh.vertices = self._spline.evaluate(
            self._q_vertices
        )
        self._logd("FFD successful.")

        self._is_calculated = True

    @property
    def control_points(self):
        """
        Returns current spline's control points. The control points can be
        directly updated with this. Please use carefully! After calling this
        'self._is_calculated' is not trackable anymore so deformation
        calculation is performed every time.

        Returns
        --------
        self._spline.control_points: np.ndarray
        """
        self._is_calculated_trackable = False
        return self._spline.control_points

    @control_points.setter
    def control_points(self,
                       control_points: Union[List[List[float]], np.ndarray]
                       ):
        """
        Sets control points and deforms mesh.

        Parameters
        -----------
        control_points: np.ndarray

        Returns
        --------
        None
        """
        assert self._spline.control_points.shape == control_points.shape,\
            "Given control points' shape does not match current ones!"

        self._spline.control_points = control_points.copy()
        self._logd("Set new control points.")
        self._is_calculated = False
        # trackable true since cp overwritten since last getter call
        self._is_calculated_trackable = True

    def elevate_degree(self, *args, **kwargs):
        """
        Wrapper for Spline.elevate_degree

        Parameters
        -----------
        *args:
        **kwargs:

        Returns
        --------
        None
        """
        self._spline.elevate_degree(*args, **kwargs)

    def insert_knots(self, parametric_dimension, knots):
        """
        Wrapper for Spline.insert_knots

        Parameters
        -----------
        *args:
        **kwargs:

        Returns
        --------
        None
        """
        if "knot_vectors" in self._spline.required_properties:
            raise NotImplementedError(
                "Can not perform knot insertion on Bezier spline.")
        # scale knots from the original bounds into the new bounds
        dim_bounds = self._orig_para_dim_ranges[parametric_dimension]
        knots = (
            (np.array(knots)-dim_bounds[0])
            / (dim_bounds[-1]-dim_bounds[0])
        )
        self._spline.insert_knots(parametric_dimension, knots)

    def remove_knots(self, parametric_dimension, knots, tolerance=1e-8):
        """
        Wrapper for Spline.remove_knots

        Parameters
        -----------
        *args:
        **kwargs:

        Returns
        --------
        None
        """
        if "knot_vectors" in self._spline.required_properties:
            raise NotImplementedError(
                "Can not perform knot insertion on Bezier spline.")
        # scale knots from the original bounds into the new bounds
        dim_bounds = self._orig_para_dim_ranges[parametric_dimension]
        knots = (
            (np.array(knots)-dim_bounds[0])
            / (dim_bounds[-1]-dim_bounds[0])
        )
        self._spline.remove_knots(
            parametric_dimension, knots, tolerance=tolerance)
        self._is_calculated = False

    def reduce_degree(self, *args, **kwargs):
        """
        Wrapper for Spline.reduce_degree

        Parameters
        -----------
        *args:
        **kwargs:

        Returns
        --------
        None
        """
        self._spline.reduce_degree(*args, **kwargs)
        self._is_calculated = False

    # The '*' prevents the title to be given as a positional argument
    def show(
            self, *, return_showable: bool = False,
            return_discrete: bool = False,
            title: str = "gustaf - FFD", **kwargs) -> Any:
        """
        Visualize. Shows the deformed mesh and the current spline. Currently
        visualization is limited to vedo.

        Parameters
        ----------
        title: str
            Title of the vedo window. Defaults to "gustaf - FFD".
        return_showable: bool
            If true returns a dict of the showable items. Defaults to False.
        return_discrete: bool
            Return dict of gustaf discrete objects, for example,
            {Vertices, Edges, Faces}, instead of opening a window.
            Defaults to False.
        kwargs: Any
            Arbitrary keyword arguments. These are passed onto the vedo
            functions. Please be aware, that no checking of these are performed
            in this function.

        Returns
        -------
        Any:
            Returns, if applicable, the vedo plotter. 'close=False' as argument
            to get the plotter.
        """
        backend = kwargs.get("backend", None)
        if backend is None:
            backend = settings.VISUALIZATION_BACKEND

        if backend != "vedo":
            raise NotImplementedError(
                "Visualization of the FFD is not available for the chosen"
                f"visualization framework -{settings.VISUALIZATION_BACKEND}-."
                " Please choose vedo to visualize."
            )
        original_mesh = self._mesh.copy()
        original_mesh.vertices = self._q_vertices
        vis_dict = dict()
        if original_mesh.kind == "volume":
            orig_mesh_outer_faces = Faces(
                original_mesh.vertices,
                original_mesh.get_faces()[
                    original_mesh.get_surfaces()]
            )
            mesh_outer_faces = Faces(
                self.mesh.vertices,
                self.mesh.get_faces()[
                    self.mesh.get_surfaces()]
            )
            vis_dict.update(
                original_mesh=[
                    "Original Mesh",
                    original_mesh,
                    orig_mesh_outer_faces.toedges(unique=True)
                ]
            )
            vis_dict.update(
                deformed_mesh=[
                    "Deformed Mesh with Spline",
                    mesh_outer_faces.toedges(unique=True),
                    *self._spline.showable(
                        return_discrete=return_discrete
                    ).values()]
            )
        else:
            original_dict = {
                "ffd_title": "Original Mesh",
                "ffd_mesh": original_mesh,
                "ffd_mesh_edges": original_mesh.toedges(unique=True)
            }
            vis_dict.update(
                original_mesh=original_dict
            )
            deformed_dict = {
                "ffd_title": "Deformed Mesh with Spline",
                "ffd_mesh": self.mesh.toedges(unique=True).showable(),
            }
            deformed_dict.update(
                **self._spline.showable(
                    return_discrete=return_discrete
                ))
            vis_dict.update(
                deformed_mesh=deformed_dict
            )
        if return_discrete or return_showable:
            return vis_dict
        return show_vedo(
            *vis_dict.values(),
            title=title, **kwargs
        )

    def showable(self, *args, **kwargs):
        """
        Returns a dictionary of showable items to describe the FFD at the
        current state.

        See show() for more information. This function redirects to it directly
        with the return_showable keyword set to True.
        """
        self.show(*args, return_showable=True, **kwargs)

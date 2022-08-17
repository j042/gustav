"""gustaf/gustaf/io/nutils.py
io functions for nutils.
"""

import os
import struct

import numpy as np

from gustaf.vertices import Vertices
from gustaf.faces import Faces
from gustaf.volumes import Volumes
from gustaf.io.ioutils import abs_fname, check_and_makedirs
from gustaf.utils import log
from gustaf.io import mixd

def load(fname):
    """
    nutils load.
    Loads a nutils (np.savez) file and returns a Gustaf Mesh.

    Parameters
    -----------
    fname: str
      The npz file needs the following keys: nodes, cnodes, coords, tags, btags, ptags.
    """
    npzfile = np.load(fname, allow_pickle=True)
    nodes = npzfile['nodes']
    cnodes = npzfile['cnodes']
    coords = npzfile['coords']
    tags = npzfile['tags'].item()
    btags = npzfile['btags'].item()
    ptags = npzfile['ptags'].item()

    vertices = coords

    # connec
    simplex = True
    connec = None

    if vertices.shape[1]==2:
        volume = False 
    else:
        volume = True

    try:
        connec = nodes
    except:
        log.debug("Error")

    # reshape connec
    if connec is not None:
        ncol = int(3) if simplex and not volume else int(4)
        connec = connec.reshape(-1, ncol)
        mesh = Volumes(vertices, connec) if volume else Faces(vertices, connec)

    mesh.BC = btags
    return mesh

def export(fname, mesh):
    """
    Export in Nutils format. Files are saved as np.savez().
    Supports triangle,and tetrahedron Meshes.

    Parameters
    -----------
    mesh: Faces or Volumes
    fname: str

    Returns
    --------
    None
    """

    dic = to_nutils_simplex(mesh)

    # prepare export location
    fname = abs_fname(fname)
    check_and_makedirs(fname)

    np.savez(fname, **dic)


def to_nutils_simplex(mesh):
    """
    Converts a Gustaf_Mesh to a Dictionary, which can be interpreted by 
    nutils.mesh.simplex(**to_nutils_simplex(mesh)). Only work for 
    Triangles and Tetrahedrons!

    Parameters
    -----------
    mesh: Faces or Volumes

    Returns
    --------
    dic_to_nutils: dict
    """

    vertices = mesh.vertices
    faces = mesh.get_faces()		
    whatami = mesh.get_whatami()

    #In 2D, element = face. In 3D, element = volume.
    if whatami.startswith("tri"):
        dimension = 2
        permutation = [1,2,0]
        elements = faces
    elif whatami.startswith("tet"):
        dimension = 3
        permutation = [2,3,1,0]
        volumes = mesh.volumes				
        elements = volumes     
    else:
        raise TypeError('Only Triangle and Tetrahedrons are accepted.') 

    dic_to_nutils = dict()
    
    #Sort the Node IDs for each Element. 
    elements_sorted = np.zeros(elements.shape)
    sort_array = np.zeros(elements.shape)
    
    for index, row in enumerate(elements):
        elements_sorted[index] = np.sort(row)	
        sort_array[index] = np.argsort(row)
    elements_sorted = elements_sorted.astype(int)	
    sort_array = sort_array.astype(int)

    #Let`s get the Boundaries
    bcs = dict()
    bcs_in = mixd.make_mrng(mesh)	
    bcs_in = np.ndarray.reshape(bcs_in,(int(len(bcs_in)/(dimension + 1)),(dimension + 1)))

    bound_id = np.unique(bcs_in)
    bound_id = bound_id[bound_id > 0]

    #Reorder the mrng according to nutils permutation: swap collumns
    bcs_in[:,:] = bcs_in[:,permutation]	
        
    #Let's reorder the bcs file with the sort_array
    bcs_sorted = np.zeros(bcs_in.shape)	
    for index, sorts in enumerate(sort_array):
        bcs_sorted[index] = bcs_in[index][sorts]
    bcs_sorted = bcs_sorted.astype(int)
        
    for bi in bound_id:
        temp = []
        for elid, el in enumerate(bcs_sorted):
            for index, edge in enumerate(el):
                if bi == edge:
                    temp.append([elid,index])
        bcs.update(
            {str(bi)		:	np.array(temp)}
        )

    dic_to_nutils.update(   
        {   'nodes'     :   elements_sorted,
            'cnodes'    :   elements_sorted,
            'coords'    :   vertices,
            'tags'      :   {},
            'btags'     :   bcs	,
            'ptags'     :   {}
        }   
    )

    return dic_to_nutils


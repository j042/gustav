import numpy as np

import gustaf as gus

if __name__ == "__main__":
    # define coordinates
    v = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
        ]
    )
    # define tet connectivity
    tv = np.array(
        [
            [0, 2, 7, 3],
            [0, 2, 6, 7],
            [0, 6, 4, 7],
            [5, 0, 4, 7],
            [5, 0, 7, 1],
            [7, 0, 3, 1],
        ]
    )
    # define hexa connectivity
    hv = np.array([[0, 1, 3, 2, 4, 5, 7, 6]])

    # init tet
    tet = gus.Volumes(
        vertices=v,
        volumes=tv,
    )

    # init hexa
    hexa = gus.Volumes(
        vertices=v,
        volumes=hv,
    )

    # show
    tet.show()

    # green tet
    tet.show_options["c"] = "green"
    tet.show()

    # display vertexdata
    # assign values to vertexdata
    hexa.vertexdata["arange"] = np.arange(len(v))
    # set vertexdata to plot
    hexa.show_options["dataname"] = "arange"
    hexa.show()

MeshAlgo3D = {"Delaunay": 1, "Initial": 3, "Frontal": 4, "MMG3D": 7, "HXT": 10}


def get_allowed_algo() -> list:
    """
    return allowed 2D algo
    """
    return list(MeshAlgo3D.keys())


def get_algo(name: str):
    return MeshAlgo3D[name]


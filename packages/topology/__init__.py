"""
Topology module for mesh preprocessing, sharp edge detection, and region partitioning.
"""

from .preprocessing import (
    compute_face_normals,
    build_edge_face_map,
    detect_sharp_edges,
    compute_dihedral_angles,
    segment_smooth_regions,
    MeshPreprocessor
)

__all__ = [
    'compute_face_normals',
    'build_edge_face_map',
    'detect_sharp_edges',
    'compute_dihedral_angles',
    'segment_smooth_regions',
    'MeshPreprocessor'
]
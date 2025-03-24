"""
pt
==

Parallel Transport Layers.
"""

import torch

from ..base.paths import PathBuffer


class v_PT(torch.nn.Module):
    """
    Parallel Transport Layer for objects that transform vector-like.

    It has no weights.

    paths is a list of paths. Every path is a list [(direction, nhops)].
    An empty list is the path that does not perform any hops.

    For a PT layer with all 0- and 1-hop paths, construct the layer like this::

        U = torch.tensor(np.load("path/to/gauge/config.npy"))

        paths = [[]] + [[(mu, 1)] for mu in range(4)] + [[(mu, -1)] for mu in range(4)]
        layer = v_PT(paths, U)
    """

    def __init__(self, paths, U, **path_buffer_kwargs):
        super().__init__()
        self.n_feature_in = len(paths)
        self.n_feature_out = len(paths)
        self.path_buffer_kwargs = path_buffer_kwargs
        self.path_buffers = [
            PathBuffer(U, pi, **path_buffer_kwargs) for pi in paths
        ]

    def forward(self, features_in):
        if features_in.shape[0] != self.n_feature_in:
            raise ValueError(
                f"shape mismatch: got {features_in.shape[0]} but expected {self.n_feature_in}"
            )

        features_out = [None] * self.n_feature_out

        for i, p in enumerate(self.path_buffers):
            features_out[i] = p.v_transport(features_in[i])

        return torch.stack(features_out)

    def reverse(self, features_in):
        if features_in.shape[0] != self.n_feature_in:
            raise ValueError(
                f"shape mismatch: got {features_in.shape[0]} but expected {self.n_feature_in}"
            )

        features_out = [None] * self.n_feature_out

        for i, p in enumerate(self.path_buffers):
            features_out[i] = p.v_reverse_transport(features_in[i])

        return torch.stack(features_out)

    def gauge_transform_using_transformed(self, U_transformed):
        """
        Update the v_PT layer: The old gauge field U is replaced by
        U_transformed. The weights are kept.

        NOTE: This does not create a transformed copy of the layer!
              Instead the layer is updated.

        Mostly used for testing.
        """
        for i, pi in enumerate(self.path_buffers):
            self.path_buffers[i] = PathBuffer(
                U_transformed, pi.path, **self.path_buffer_kwargs
            )

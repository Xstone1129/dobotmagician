"""Dobot Magician palletizing trajectory-learning algorithms."""

from .gmr_primitives import BGMMGMRProMP, GMMGMRDMP, GMMGMRSegmentedDMP, IncGMMGMRDMP

__all__ = [
    "BGMMGMRProMP",
    "GMMGMRDMP",
    "GMMGMRSegmentedDMP",
    "IncGMMGMRDMP",
]

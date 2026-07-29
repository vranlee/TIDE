from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .yolo import get_pose_net as _get_pose_net


def get_pose_net(*args, **kwargs):
    return _get_pose_net(*args, **kwargs)

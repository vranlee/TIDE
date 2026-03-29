import cv2
import numpy as np
import scipy
import lap
from scipy.spatial.distance import cdist

from cython_bbox import bbox_overlaps as bbox_ious
from tracking_utils import kalman_filter

import math

import time


def merge_matches(m1, m2, shape):
    O, P, Q = shape
    m1 = np.asarray(m1)
    m2 = np.asarray(m2)

    M1 = scipy.sparse.coo_matrix((np.ones(len(m1)), (m1[:, 0], m1[:, 1])), shape=(O, P))
    M2 = scipy.sparse.coo_matrix((np.ones(len(m2)), (m2[:, 0], m2[:, 1])), shape=(P, Q))

    mask = M1 * M2
    match = mask.nonzero()
    match = list(zip(match[0], match[1]))
    unmatched_O = tuple(set(range(O)) - set([i for i, j in match]))
    unmatched_Q = tuple(set(range(Q)) - set([j for i, j in match]))

    return match, unmatched_O, unmatched_Q


def _indices_to_matches(cost_matrix, indices, thresh):
    matched_cost = cost_matrix[tuple(zip(*indices))]
    matched_mask = (matched_cost <= thresh)

    matches = indices[matched_mask]
    unmatched_a = tuple(set(range(cost_matrix.shape[0])) - set(matches[:, 0]))
    unmatched_b = tuple(set(range(cost_matrix.shape[1])) - set(matches[:, 1]))

    return matches, unmatched_a, unmatched_b

def linear_assignment(cost_matrix, thresh):
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), tuple(range(cost_matrix.shape[0])), tuple(range(cost_matrix.shape[1]))
    matches, unmatched_a, unmatched_b = [], [], []
    cost, x, y = lap.lapjv(cost_matrix, extend_cost=True, cost_limit=thresh)
    for ix, mx in enumerate(x):
        if mx >= 0:
            matches.append([ix, mx])
    unmatched_a = np.where(x < 0)[0]
    unmatched_b = np.where(y < 0)[0]
    matches = np.asarray(matches)
    return matches, unmatched_a, unmatched_b


def P2PIoU(box1, box2, eps=1e-7):
    # Extract coordinates and dimensions
    x11, y11, x12, y12 = box1
    w1, h1 = x12 - x11, y12 - y11
    x21, y21, x22, y22 = box2
    w2, h2 = x22 - x21, y22 - y21

    # Calculate centers
    xc1, yc1 = (x11 + x12) / 2, (y11 + y12) / 2
    xc2, yc2 = (x21 + x22) / 2, (y21 + y22) / 2

    # Calculate traditional IoU
    x_intersection = max(0, min(x12, x22) - max(x11, x21))
    y_intersection = max(0, min(y12, y22) - max(y11, y21))
    area_intersection = x_intersection * y_intersection
    area_union = w1 * h1 + w2 * h2 - area_intersection
    iou = area_intersection / (area_union + eps)

    # Advanced distance metrics
    center_distance = math.sqrt(pow((xc2 - xc1), 2) + pow((yc2 - yc1), 2))

    # Normalize distance by average box size (important for fish of different sizes)
    avg_size = (math.sqrt(w1 * h1) + math.sqrt(w2 * h2)) / 2
    normalized_distance = center_distance / (avg_size + eps)

    # Calculate aspect ratio consistency (fish shape consistency)
    ar1, ar2 = w1 / (h1 + eps), w2 / (h2 + eps)
    ar_consistency = min(ar1, ar2) / max(ar1, ar2)

    # Size consistency penalty (fish don't suddenly change size)
    size_ratio = min(w1 * h1, w2 * h2) / (max(w1 * h1, w2 * h2) + eps)

    # Calculate enhanced P2PIoU
    distance_factor = 0.1 / (normalized_distance + eps)
    shape_factor = 0.05 * ar_consistency + 0.05 * size_ratio
    # p2piou = iou + distance_factor + shape_factor

    if iou > 0.7:
        # If overlap is high, give more weight to IoU
        p2piou = iou
    else:
        # If overlap is low, point-to-point distance becomes more important
        p2piou = iou + 0.5 * (distance_factor + shape_factor)

    return p2piou

def iou_for_cython(boxes, query_boxes, xywh=True, scale=1, eps=1e-7):
    N = boxes.shape[0]
    K = query_boxes.shape[0]
    overlaps = np.zeros((N, K), dtype=np.float64)

    for i in range(N):
        for j in range(K):
            # overlaps[i, j] = DIoU(boxes[i], query_boxes[j])
            overlaps[i, j] = P2PIoU(boxes[i], query_boxes[j], eps=eps)
            # overlaps[i, j] = CIoU(boxes[i], query_boxes[j])
            # overlaps[i, j] = shape_iou(boxes[i], query_boxes[j], xywh=xywh, scale=scale, eps=eps)
            #  SIoU(boxes[i], query_boxes[j])
    return overlaps


def ious(atlbrs, btlbrs):
    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float64)
    if ious.size == 0:
        return ious

    ious = iou_for_cython(
        np.ascontiguousarray(atlbrs, dtype=np.float64),
        np.ascontiguousarray(btlbrs, dtype=np.float64)
    )

    return ious

def iou_distance(atracks, btracks):
    """
    Compute cost based on IoU
    :type atracks: list[STrack]
    :type btracks: list[STrack]

    :rtype cost_matrix np.ndarray
    """

    if (len(atracks) > 0 and isinstance(atracks[0], np.ndarray)) or (
            len(btracks) > 0 and isinstance(btracks[0], np.ndarray)):
        atlbrs = atracks
        btlbrs = btracks
    else:
        atlbrs = [track.tlbr for track in atracks]
        btlbrs = [track.tlbr for track in btracks]
    _ious = ious(atlbrs, btlbrs)
    cost_matrix = 1 - _ious

    return cost_matrix


def embedding_distance(tracks, detections, metric='cosine'):
    """
    :param tracks: list[STrack]
    :param detections: list[BaseTrack]
    :param metric:
    :return: cost_matrix np.ndarray
    """

    cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float64)
    if cost_matrix.size == 0:
        return cost_matrix
    det_features = np.asarray([track.curr_feat for track in detections], dtype=np.float64)
    # for i, track in enumerate(tracks):
    # cost_matrix[i, :] = np.maximum(0.0, cdist(track.smooth_feat.reshape(1,-1), det_features, metric))
    track_features = np.asarray([track.smooth_feat for track in tracks], dtype=np.float64)
    cost_matrix = np.maximum(0.0, cdist(track_features, det_features, metric))  # Nomalized features
    return cost_matrix

def gate_cost_matrix(kf, cost_matrix, tracks, detections, only_position=False):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xyah() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(
            track.mean, track.covariance, measurements, only_position)
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
    return cost_matrix

def fuse_motion(kf, cost_matrix, tracks, detections, only_position=False, lambda_=0.98):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xyah() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(
            track.mean, track.covariance, measurements, only_position, metric='maha')
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
        cost_matrix[row] = lambda_ * cost_matrix[row] + (1 - lambda_) * gating_distance
    return cost_matrix

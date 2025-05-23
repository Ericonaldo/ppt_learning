import numpy as np
from scipy.spatial.transform import Rotation as R

left_T_base = np.ascontiguousarray(
    [
        [-0.99337418, -0.07595198, 0.0862499, 0.36654217],
        [-0.11333327, 0.52293955, -0.84480163, 0.59254171],
        [0.01906087, -0.84897911, -0.52808253, 0.41738771],
        [0.0, 0.0, 0.0, 1.0],
    ]
).astype(np.float32)


right_T_base = np.ascontiguousarray(
    [
        [0.99091838, 0.04761393, -0.12575242, 0.58782787],
        [0.13285233, -0.4910695, 0.86093031, -0.67237814],
        [-0.02076091, -0.86981818, -0.49293542, 0.43181249],
        [0.0, 0.0, 0.0, 1.0],
    ]
).astype(np.float32)

wrist_T_tcp = np.ascontiguousarray(
    [
        [0.12872182, -0.99136592, -0.02498592, 0.1308883],
        [0.99092303, 0.1275979, 0.04231235, -0.04321031],
        [-0.03875887, -0.03020564, 0.99879195, -0.0233101],
        [0.0, 0.0, 0.0, 1.0],
    ]
).astype(np.float32)


left_T_base_T = np.ascontiguousarray(left_T_base.T[:3, :3])
right_T_base_T = np.ascontiguousarray(right_T_base.T[:3, :3])


# dictionary for multi-processing
calib = {
    "left_cam": {
        "transform": left_T_base,
        "rotation": left_T_base_T,
    },
    "right_cam": {
        "transform": right_T_base,
        "rotation": right_T_base_T,
    },
    "wrist_cam": {
        "transform": wrist_T_tcp,
        "rotation": None,
    },
}

camera_0_pos = (1.14694946, -0.47459371, 0.48398427)
camera_0_quat = (-0.4298767, 0.60639758, 0.66690606, 0.05219497)
camera_0_pos = (1.14324971, -0.46333842,  0.48575002)
camera_0_quat = (-0.42605169,  0.61044048,  0.66577936,  0.05079589)
camera_0_transform = np.eye(4)
camera_0_transform[:3, 3] = camera_0_pos
camera_0_transform[:3, :3] = R.from_quat(camera_0_quat, scalar_first=True).as_matrix()


camera_1_pos = (1.11234529, 0.15538119, 0.91406151)
camera_1_quat = (-0.19794745, 0.68791335, 0.68906353, -0.11306406)
camera_1_transform = np.eye(4)
camera_1_transform[:3, 3] = camera_1_pos
camera_1_transform[:3, :3] = R.from_quat(camera_1_quat, scalar_first=True).as_matrix()

calib_ur = {
    "camera_0": {
        "transform": camera_0_transform,
        "rotation": np.ascontiguousarray(camera_0_transform[:3, :3].T),
    },
    "camera_1": {
        "transform": camera_1_transform,
        "rotation": np.ascontiguousarray(camera_1_transform[:3, :3].T),
    },
}

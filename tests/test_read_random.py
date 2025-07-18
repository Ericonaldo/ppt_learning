import time
import numpy as np
import lance
import zarr
from tqdm import tqdm
import random

ds = lance.dataset("/mnt/bn/robot-minghuan-datasets-lq/xiaoshen/datasets/ur5_put_bowl_in_microwave_and_close/one_camera_no_crop_642_no_yaw_lance/data.lance/")
print(ds.schema.names)
keys = ['actions', 'obs/eef_pos', 'obs/eef_quat', 'obs/joint_pos', 'obs/joint_vel', 'obs/normalized_gripper_pos',]


import memory_profiler

@memory_profiler.profile
def process_data():
    start_time = time.time()
    table = ds.to_table(columns=keys)
    print(f"Execution time: {time.time() - start_time} seconds")
    data = {}
    for key in keys:
        data[key] = np.array(table[key])
    return data

data = process_data()
# print(data)
# num = 100
# length = ds.count_rows()
# keys = ['actions', 'obs/eef_pos', 'obs/eef_quat', 'obs/joint_pos', 'obs/joint_vel', 'obs/normalized_gripper_pos', 'obs/pointcloud/pos']

# zarr_store = zarr.DirectoryStore("/mnt/bn/robot-minghuan-datasets-lq/xiaoshen/datasets/ur5_put_bowl_in_microwave_and_close/one_camera_no_crop_642_no_yaw.zarr/")
# zarr_root = zarr.Group(zarr_store)
# start_time = time.time()
# for i in tqdm(range(num)):
#     for key in keys:
#         if key in ["row_id"]:
#             continue
#         zarr_root["data"][key][random.randint(0, length - 1)]
# print((time.time() - start_time) / num)

# start_time = time.time()
# for i in tqdm(range(num)):
#     for key in keys:
#         if key in ["row_id"]:
#             continue
#         row = ds.take([random.randint(0, length - 1)], keys)
#         ds_data = row.column(key)
#         np.stack(ds_data.to_numpy())
# print((time.time() - start_time) / num)
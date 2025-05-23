import time
import cv2
import os, sys
import numpy as np
from pathlib import Path
import pyrealsense2 as rs
import numpy as np
import time
import os 
from pathlib import Path
import random
import re

from ppt_learning.paths import *

sys.path.append(f"{PPT_DIR}/third_party/")

MODEL_PATH = f'{PPT_DIR}/../models/depth/480pnoise-e096-s397312.ckpt'
WIDTH, HEIGHT = 672, 504

def get_log_folder(log_root: str, use_model: bool = False):
    tag = "model" if use_model else "raw"
    log_folder = Path(log_root) / f'{time.strftime("%Y-%m-%d_%H-%M-%S")}-{tag}'
    os.makedirs(log_folder, exist_ok=True)
    return log_folder

def get_json_log_path(log_folder: Path):
    log_folder = Path(log_folder)
    files = os.listdir(log_folder)
    pattern = r'log-(\d{6})-\d{4}'
    existing_numbers = [int(re.match(pattern, file).group(1)) for file in files if re.match(pattern, file)]
    if not existing_numbers:
        next_number = 1
    else:
        existing_numbers.sort()
        next_number = existing_numbers[-1] + 1
    random_id = random.randint(1000, 9999)
    dir_path = log_folder / f"log-{next_number:06d}-{random_id}"
    os.makedirs(dir_path, exist_ok=True)
    new_filename = f"traj.json"
    return dir_path / new_filename
# this code is tested for multi-camera setup 
# pipeline = rs.pipeline()
# rsconfig = rs.config()
# pipeline_wrapper = rs.pipeline_wrapper(pipeline)
# pipeline_profile = rsconfig.resolve(pipeline_wrapper)
# device = pipeline_profile.get_device()

def get_serial_numbers():
    ctx = rs.context()
    if len(ctx.devices) > 0:
        for d in ctx.devices:
            print('Found device: ',
                d.get_info(rs.camera_info.name), ' ',
                d.get_info(rs.camera_info.serial_number))
    else:
        print("No Intel Device connected")

class MultiRealSenseCamera:
    def __init__(self, image_width=640, image_height=480, fps=30):
        super().__init__()
        # set initial pipelines and configs
        self.serial_numbers, self.device_idxs = self.get_serial_numbers()
        self.total_cam_num = len(self.serial_numbers)   
        self.pipelines = [None] * self.total_cam_num
        self.configs = [None] * self.total_cam_num

        # set resolutions and fps 
        self.image_width = image_width
        self.image_height = image_height
        self.fps = fps

        # set pipelines and configs
        for i, serial_number in zip(range(0, self.total_cam_num), self.serial_numbers):
            self.pipelines[i] = rs.pipeline()
            self.configs[i] = rs.config()
            self.configs[i].enable_device(serial_number)
            self.configs[i].enable_stream(rs.stream.depth, self.image_width, self.image_height, rs.format.z16, self.fps)
            self.configs[i].enable_stream(rs.stream.color, self.image_width, self.image_height, rs.format.rgb8, self.fps)
    
        # Start streaming
        self.sensors = [None] * self.total_cam_num
        self.cfgs = [None] * self.total_cam_num
        self.depth_scales = [None] * self.total_cam_num
        # set master & slave 
        master_or_slave = 1
        for i in range(0, self.total_cam_num):
            depth_sensor = self.ctx.devices[self.device_idxs[i]].first_depth_sensor()
            color_sensor = self.ctx.devices[self.device_idxs[i]].first_color_sensor()
            color_sensor.set_option(rs.option.auto_exposure_priority, 0)
            if i == 0:
                depth_sensor.set_option(rs.option.inter_cam_sync_mode, master_or_slave)
                master_or_slave = 2
            else:
                depth_sensor.set_option(rs.option.inter_cam_sync_mode, master_or_slave)

            self.cfgs[i] = self.pipelines[i].start(self.configs[i])
            depth_scale = self.cfgs[i].get_device().first_depth_sensor().get_depth_scale()
            self.depth_scales[i] = depth_scale
            # sensor = self.pipelines[i].get_active_profile().get_device().query_sensors()[1]
            # sensor.set_option(rs.option.exposure, 330)
    
    def undistorted_rgbd(self):
        depth_frame = [None] * self.total_cam_num	
        color_frame = [None] * self.total_cam_num
        depth_image = [None] * self.total_cam_num
        color_image = [None] * self.total_cam_num
        for i in range(0, self.total_cam_num):
            frame = self.pipelines[i].wait_for_frames()
            align_frame = rs.align(rs.stream.color).process(frame)
            depth_frame[i] = align_frame.get_depth_frame() 
            color_frame[i] = align_frame.get_color_frame()
            depth_image[i] = np.asanyarray(depth_frame[i].get_data()) * self.depth_scales[i]
            color_image[i] = np.asanyarray(color_frame[i].get_data())
        return color_image, depth_image

    def undistorted_rgb(self):
        color_frame = [None] * self.total_cam_num
        color_image = [None] * self.total_cam_num
        for i in range(0, self.total_cam_num):
            frame = self.pipelines[i].wait_for_frames()
            align_frame = rs.align(rs.stream.color).process(frame)
            color_frame[i] = align_frame.get_color_frame()
            color_image[i] = np.asanyarray(color_frame[i].get_data())
        return color_image

    def get_serial_numbers(self):
        serial_numbers = []
        device_idxs = []
        self.ctx = rs.context()
        if len(self.ctx.devices) > 0:
            for j, d in enumerate(self.ctx.devices):
                name = d.get_info(rs.camera_info.name)
                serial_number = d.get_info(rs.camera_info.serial_number)
                print(f"Found device: {name} {serial_number}")
                serial_numbers.append(serial_number)
                device_idxs.append(j)
        else:
            print("No Intel Device connected")
        return serial_numbers, device_idxs

    def get_intrinsic_color(self):
        intrinsic = [None] * self.total_cam_num
        for i in range(0, self.total_cam_num):
            profile = self.cfgs[i].get_stream(rs.stream.color).as_video_stream_profile()
            intr = profile.get_intrinsics()
            intrinsic[i] = {
                "width": intr.width,
                "height": intr.height,
                "fx": intr.fx,
                "fy": intr.fy,
                "ppx": intr.ppx,
                "ppy": intr.ppy
            }
        return intrinsic
    
    def get_intrinsic_depth(self):
        intrinsic = [None] * self.total_cam_num
        for i in range(0, self.total_cam_num):
            profile = self.cfgs[i].get_stream(rs.stream.depth).as_video_stream_profile()
            intr = profile.get_intrinsics()
            intrinsic[i] = {
                "width": intr.width,
                "height": intr.height,
                "fx": intr.fx,
                "fy": intr.fy,
                "ppx": intr.ppx,
                "ppy": intr.ppy
            }
        return intrinsic

def save_images(images, images_dir, use_model=False, intrinsics=None, headless=False, save=True):
    tmp_colors, tmp_depths = images
    if use_model:
        if 'WORKSPACE' not in os.environ:
            os.environ['WORKSPACE'] = f'{PPT_DIR}/third_party/ranging_depth'
        import torch
        from ranging_anything.compute_metric import (
            interp_depth_rgb,
            recover_metric_depth_ransac,
            colorize_depth_maps,
        )
        from ppt_learning.utils.ranging_depth_utils import get_model, model_infer
        depth_model = get_model(MODEL_PATH).to("cuda" if torch.cuda.is_available() else "cpu")
        depth_model.eval()

        for i in range(len(tmp_depths)):
            tmp_depths[i] = interp_depth_rgb(tmp_depths[i], cv2.cvtColor(tmp_colors[i], cv2.COLOR_RGB2GRAY))
            tmp_depths[i] = cv2.resize(tmp_depths[i], (WIDTH, HEIGHT), interpolation=cv2.INTER_NEAREST)
            tmp_colors[i] = cv2.resize(tmp_colors[i], (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)

        depths = torch.from_numpy(np.stack(tmp_depths, axis=0)).float().unsqueeze(1)
        colors = torch.from_numpy(np.stack(tmp_colors, axis=0)).permute(0, 3, 1, 2).float()
        tmp_depths = model_infer(
            depth_model, colors, depths, True
        ).squeeze()

    now_time = int(time.time() * 1000)
    assert len(tmp_colors) == len(tmp_depths)
    if save:
        if intrinsics is not None:
            assert len(intrinsics) == len(tmp_colors)
            np.savez(images_dir / f"intrinsics.npz", intrinsics)
        for i in range(len(tmp_colors)):
            os.makedirs(images_dir / f"color_{i}", exist_ok=True)
            os.makedirs(images_dir / f"depth_{i}", exist_ok=True)
            cv2.imwrite(str(images_dir / f"color_{i}" / f"{now_time}.png"), cv2.cvtColor(tmp_colors[i], cv2.COLOR_RGB2BGR))
            np.save(str(images_dir / f"depth_{i}" / f"{now_time}.npy"), tmp_depths[i])

    if not headless:
        for i in range(len(tmp_colors)):
            depth = tmp_depths[i]
            depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
            depth = cv2.applyColorMap(depth.astype(np.uint8), cv2.COLORMAP_JET)
            cv2.imshow(f"Color {i}", cv2.cvtColor(tmp_colors[i], cv2.COLOR_RGB2BGR))
            cv2.imshow(f"Depth {i}", depth)
    return now_time

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="store_true")

    args = parser.parse_args()

    # 设置数据保存目录
    data_dir = get_log_folder("/home/minghuan/ppt_learning/logs/photos", args.model)

    # 初始化RealSense摄像头
    multi_camera = MultiRealSenseCamera(fps=30, image_width=640, image_height=480)

    i = 1
    # 主循环
    while True:
        # 获取并保存图像
        images = multi_camera.undistorted_rgbd()
        # print intrinsics
        print(multi_camera.get_intrinsic_color())
        if i % 120 == 0:
            save_images(images, data_dir, intrinsics=multi_camera.get_intrinsic_color(), use_model=args.model, headless=True, save=True)
        # 控制帧率
        time.sleep(1/60.0)
        i += 1
        if i > 1300:
            break

    # 清理资源
    cv2.destroyAllWindows()

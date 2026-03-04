import uuid
import asyncio
import subprocess
import os
from .log import logger


async def resize_video(input_file, output_file, width=720, height=1440):
    """一行代码完成视频尺寸调整"""
    cmd = (
        f'/usr/bin/ffmpeg -y -i "{input_file}" '
        f'-vf scale={width}:{height} '
        f'-r 25 '
        f'-c:a copy '
        f'"{output_file}"'
    )
    try:
        process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f'视频转换成功: {input_file} -> {output_file}')
            return output_file
        else:
            logger.error(f'视频转换失败: {input_file}, 错误: {stderr.decode()}')
            return None
    except Exception as e:
        logger.error(f'视频转换异常: {input_file}, 错误: {e}')
        return None


async def resize_video_in_memory(video_data, width=720, height=1440):
    """直接处理内存中的视频数据，返回转换后的 bytes"""
    # 使用uuid生成唯一的临时文件名
    unique_id = str(uuid.uuid4())
    tmp_input_path = f'/tmp/video_input_{unique_id}.mp4'
    tmp_output_path = f'/tmp/video_output_{unique_id}.mp4'
    # 清理可能存在的旧文件
    if os.path.exists(tmp_input_path):
        os.unlink(tmp_input_path)
    if os.path.exists(tmp_output_path):
        os.unlink(tmp_output_path)
    try:
        # 写入输入文件
        with open(tmp_input_path, 'wb') as f:
            f.write(video_data)
        # 转换
        result = await resize_video(tmp_input_path, tmp_output_path, width, height)
        if not result:
            return None
        # 读取转换后的文件
        with open(tmp_output_path, 'rb') as f:
            output_data = f.read()
        return output_data
    finally:
        # 清理临时文件
        if os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)

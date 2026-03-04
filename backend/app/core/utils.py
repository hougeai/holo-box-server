import asyncio
import subprocess
from .log import logger


async def resize_video(input_file, output_file, width=720, height=1440):
    """一行代码完成视频尺寸调整"""
    cmd = (
        f'/usr/bin/ffmpeg -i "{input_file}" ' f'-vf scale={width}:{height} ' f'-r 25 ' f'-c:a copy ' f'"{output_file}"'
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

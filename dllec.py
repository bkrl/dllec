#!/usr/bin/python3

# SPDX-FileCopyrightText: 2023 Alexander Zhang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import time

from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
from yt_dlp.utils import prepend_extension, replace_extension


class FFmpegChangeSpeedPP(FFmpegPostProcessor):
    def __init__(self, downloader=None, output_ext="mkv", speed=2.0):
        super().__init__(downloader)
        self.output_ext = output_ext
        self.speed = speed

    def run(self, info):
        orig_path = path = info["filepath"]
        temp_path = new_path = replace_extension(path, self.output_ext, info["ext"])

        if new_path == path:
            orig_path = prepend_extension(path, "orig")
            temp_path = prepend_extension(path, "temp")

        self.to_screen(f"Changing speed to {self.speed}; Destination: {new_path}")
        self.real_run_ffmpeg(
            [(path, ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"])],
            [
                (
                    temp_path,
                    [
                        "-vf",
                        f"setpts=PTS/{self.speed}",
                        "-af",
                        f"atempo={self.speed}",
                        "-c:v",
                        "vp9_vaapi",
                        "-c:a",
                        "libopus",
                    ],
                )
            ],
        )

        os.replace(path, orig_path)
        os.replace(temp_path, new_path)
        info["filepath"] = new_path
        info["format"] = info["ext"] = self.output_ext

        if info.get("filetime") is not None:
            self.try_utime(
                new_path,
                time.time(),
                info["filetime"],
                errnote="Cannot update utime of new file",
            )

        return [orig_path], info


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-o", "--output")
    parser.add_argument("-s", "--speed", default=2.0, type=float)
    args = parser.parse_args()

    ydl_args = {"prefer_free_formats": True}
    if args.output is not None:
        output_name, output_ext = os.path.splitext(args.output)
        output_ext = output_ext[1:]
        ydl_args["outtmpl"] = {"default": output_name + ".%(ext)s"}
    else:
        output_ext = "mkv"

    with YoutubeDL(ydl_args) as ydl:
        ydl.add_post_processor(
            FFmpegChangeSpeedPP(output_ext=output_ext, speed=args.speed)
        )
        ydl.download([args.url])

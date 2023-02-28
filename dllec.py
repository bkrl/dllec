#!/usr/bin/python3

# SPDX-FileCopyrightText: 2023 Alexander Zhang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import time

from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
from yt_dlp.utils import prepend_extension, replace_extension


class FFmpegDoubleSpeedPP(FFmpegPostProcessor):
    def __init__(self, downloader=None, output_ext="mkv"):
        super().__init__(downloader)
        self.output_ext = output_ext

    def run(self, info):
        orig_path = path = info["filepath"]
        temp_path = new_path = replace_extension(path, self.output_ext, info["ext"])

        if new_path == path:
            orig_path = prepend_extension(path, "orig")
            temp_path = prepend_extension(path, "temp")

        self.to_screen(f"Doubling speed; Destination: {new_path}")
        self.real_run_ffmpeg(
            [(path, ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"])],
            [
                (
                    temp_path,
                    [
                        "-vf",
                        "setpts=0.5*PTS",
                        "-af",
                        "atempo=2",
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
    args = parser.parse_args()

    ydl_args = {"prefer_free_formats": True}
    if args.output is not None:
        output_name, output_ext = os.path.splitext(args.output)
        ydl_args["outtmpl"] = {"default": output_name + ".%(ext)s"}
    else:
        output_ext = None

    with YoutubeDL(ydl_args) as ydl:
        ydl.add_post_processor(
            FFmpegDoubleSpeedPP(output_ext=output_ext[1:])
            if output_ext is not None
            else FFmpegDoubleSpeedPP()
        )
        ydl.download([args.url])

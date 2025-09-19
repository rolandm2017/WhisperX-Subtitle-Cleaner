# srt_file.py
import os
import re

from typing import List, TypedDict


class SubtitleDict(TypedDict):
    number: int
    timestamp: str
    text: str
    start_time: float
    end_time: float


class SRTFile:
    def __init__(self, input_filepath: str):
        self.filepath = input_filepath
        self.filename = os.path.basename(input_filepath)
        self.subtitles: List[SubtitleDict] = []
        self.original_content = ""

    def parse(self) -> None:
        """Parse the SRT file into subtitle objects.

        Programmer assumes the line endings are \n, not \r\n or \r
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                self.original_content = file.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(self.filepath, 'r', encoding='latin-1') as file:
                self.original_content = file.read()

        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', self.original_content.strip())

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            try:
                # Parse subtitle number
                subtitle_num = int(lines[0].strip())

                # Parse timestamp
                timestamp = lines[1].strip()

                # Parse text (everything after the timestamp)
                text = '\n'.join(lines[2:])

                subtitle_had_content = text.strip()
                # Skip empty subtitles - they're just noise from the AI model
                if subtitle_had_content:
                    subtitle: SubtitleDict = {
                        'number': subtitle_num,
                        'timestamp': timestamp,
                        'text': text,
                        'start_time': self._parse_time(timestamp.split(' --> ')[0]),
                        'end_time': self._parse_time(timestamp.split(' --> ')[1])
                    }

                    self.subtitles.append(subtitle)

            except (ValueError, IndexError) as e:
                print(
                    f"Warning: Could not parse subtitle block in {self.filename}: {block[:50]}...")
                continue

    def _parse_time(self, time_str: str) -> float:
        """Convert SRT time format to seconds"""
        try:
            time_str = time_str.strip()
            # Format: HH:MM:SS,mmm
            hours, minutes, seconds = time_str.split(':')
            seconds, milliseconds = seconds.split(',')

            total_seconds = int(hours) * 3600 + int(minutes) * \
                60 + int(seconds) + int(milliseconds) / 1000
            return total_seconds
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse timestamp: {time_str}")
            return 0.0

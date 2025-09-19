#!/usr/bin/env python3
# clean_whisperx_output.py

"""
Checks a file for .SRT files that have WhisperX outputs including some junk.

WhisperX thinks silence is time to put "Sous-titres FR" due to
the training data having such non-real dialogue transcriptions during silence.

"""

import os
import re
from typing import List, Dict, Any, TypedDict

from junk_patterns import JUNK_PATTERNS

from colors_printer import colored_print, colored_print_info_type

from srt_file import SRTFile, SubtitleDict

from shared_utils import (
    make_cleaned_srt_filename,
    make_log_with_cleaned_lines,
    make_empty_log_filename,
    remove_srt_extension
)


current_main_log_file = ""

# This is the phony patterns an array.
# An array is anything between two pointed brackets: []


class RealSubtitlesResult(TypedDict):
    removed_count: int
    subtitles_sans_bad_output: list
    empty_string_count: int


class SrtCleaner:

    def __init__(self, srt_file: SRTFile) -> None:
        self.srt_file: SRTFile = srt_file

    def find_phony_subtitles(self) -> List[SubtitleDict]:
        """Find subtitles that match phony patterns"""

        phony_subtitles: List[SubtitleDict] = []

        for subtitle in self.srt_file.subtitles:
            text = subtitle['text'].lower().strip()

            for pattern in JUNK_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    phony_subtitles.append(subtitle)
                    break

        return phony_subtitles

    def remove_junk_subtitles(self, phony_subtitles) -> RealSubtitlesResult:
        """Remove phony subtitles and optionally save cleaned file"""
        if not phony_subtitles:
            return {'removed_count': 0, 'subtitles_sans_bad_output': [], "empty_string_count": 0}

        print(
            f"\nFound {len(phony_subtitles)} phony subtitle(s) in {self.srt_file.filename}:")
        for sub in phony_subtitles:
            print(f"  - #{sub['number']}: {sub['text'][:50]}...")

        subtitles_out = []

        # Remove phony subtitles
        subtitles_out = [
            sub for sub in self.srt_file.subtitles if sub not in phony_subtitles]

        # Renumber subtitles
        for i, subtitle in enumerate(subtitles_out, 1):
            subtitle['number'] = i

        return {
            'removed_count': len(phony_subtitles),
            'subtitles_sans_bad_output': subtitles_out,
            "empty_string_count": len([x for x in subtitles_out if x["text"] == ""])
        }

    @staticmethod
    def prepare_cleaned_content_for_write(cleaned_subtitles):
        """
        I have no memory of writing the stuff that is appended, nor do I know why it must be written.
        """
        cleaned_content = []

        for subtitle in cleaned_subtitles:
            cleaned_content.append(f"{subtitle['number']}")
            cleaned_content.append(subtitle['timestamp'])
            cleaned_content.append(subtitle['text'])
            cleaned_content.append("")  # Empty line between subtitles

        # Remove the last empty line
        if cleaned_content and cleaned_content[-1] == "":
            cleaned_content.pop()

        return cleaned_content

    def save_cleaned_file(self, subtitles_ready_for_write):
        """Save the cleaned subtitles to a new file with ' - cleaned' suffix"""

        # Create new filename with -cleaned suffix
        base_name = os.path.splitext(self.srt_file.filepath)[
            0]  # Remove .srt extension
        cleaned_filepath: str = make_cleaned_srt_filename(base_name)

        with open(cleaned_filepath, 'w', encoding='utf-8') as file:
            file.write('\n'.join(subtitles_ready_for_write))

        cleaned_filename = os.path.basename(cleaned_filepath)
        colored_print("#######" * 3, 2)
        print(f"  → Cleaned file saved: {cleaned_filename}")
        colored_print("#######" * 3, 2)

        return cleaned_filepath

    def save_without_changes(self):
        cleaned_subtitles_prepared_for_write = self.prepare_cleaned_content_for_write(
            self.srt_file.subtitles)
        return self.save_cleaned_file(cleaned_subtitles_prepared_for_write)

    def create_phony_subtitles_log(self, phony_subtitles: List[SubtitleDict], input_srt_path):
        base_filename = remove_srt_extension(input_srt_path)
        if len(phony_subtitles) == 0:
            log_name = make_empty_log_filename(base_filename)
        else:
            log_name = make_log_with_cleaned_lines(base_filename)

        with open(log_name, "w") as f:
            for sub in phony_subtitles:
                f.write(sub["text"])
                f.write("\n")

        using_batch_log_file = current_main_log_file != "" and current_main_log_file.endswith(
            ".txt")
        if using_batch_log_file:
            with open(current_main_log_file, "a") as v:
                for sub in phony_subtitles:
                    v.write(sub["text"])
                    v.write("\n")

        return log_name


def clean_srt_file(input_file_path: str, dry_run: bool = True, with_logging: bool = False) -> Dict[str, Any]:
    """Process a single SRT file"""

    if not os.path.exists(input_file_path):
        print(f"Error: File '{input_file_path}' does not exist")
        return {}

    if not input_file_path.endswith('.srt'):
        print(f"Error: File '{input_file_path}' is not an SRT file")
        return {}

    input_filename = os.path.basename(input_file_path)
    print(f"\nProcessing: {input_filename}")

    try:
        srt_file = SRTFile(input_file_path)
        srt_file.parse()

        srt_cleaner = SrtCleaner(srt_file)

        print(f"  - Parsed {len(srt_file.subtitles)} subtitles")

        # Find phony subtitles
        phony_subtitles: List[SubtitleDict] = srt_cleaner.find_phony_subtitles(
        )
        if with_logging:
            log_loc = srt_cleaner.create_phony_subtitles_log(
                phony_subtitles, input_file_path)
            print("##")
            print("## MAKING LOG FILE: at location: " + log_loc)
            print("##")
        phony_count = len(phony_subtitles)

        # Show phony subtitles if found
        if phony_subtitles:
            print(f"  - Found {phony_count} PHONY subtitle(s):")
            for sub in phony_subtitles:
                print(f"    #{sub['number']}: {sub['text'][:80]}...")

            # Remove phony subtitles
            removal_result: RealSubtitlesResult = srt_cleaner.remove_junk_subtitles(
                phony_subtitles)

            srt_file.subtitles = removal_result["subtitles_sans_bad_output"]
            cleaned_subtitles_prepared_for_write = srt_cleaner.prepare_cleaned_content_for_write(
                removal_result["subtitles_sans_bad_output"])
            cleaned_filepath = srt_cleaner.save_cleaned_file(
                cleaned_subtitles_prepared_for_write)

            result = {
                'filename': input_filename,
                'filepath': input_file_path,
                'subtitle_count': len(srt_file.subtitles),
                "empty_string_count": removal_result["empty_string_count"],
                'phony_count': phony_count,
                'cleaned_file': cleaned_filepath,
                'success': True
            }

            return result
        else:
            cleaned_filepath = srt_cleaner.save_without_changes()
            result = {
                'filename': input_filename,
                'filepath': input_file_path,
                'subtitle_count': len(srt_file.subtitles),
                'phony_count': phony_count,
                'cleaned_file': cleaned_filepath,
                'success': True
            }

            return result

    except Exception as e:

        import traceback
        traceback.print_exc()
        print(e)
        print(f"  - Error processing {input_filename}: {str(e)}")
        return {
            'filename': input_filename,
            'filepath': input_file_path,
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Parse and clean a single SRT subtitle file')
    parser.add_argument('--input-file-path', dest='filepath',
                        help='Path to the SRT file to process')
    parser.add_argument('--clean', action='store_true',
                        help='Actually remove phony subtitles (default: dry run)')

    args = parser.parse_args()

    print("SRT File Cleaner (Single File)")
    print("=" * 40)
    print("Args: ", args)

    if not args.clean:
        print("Running in DRY RUN mode - file will not be modified")
        print("Use --clean flag to actually remove phony subtitles")

    result = clean_srt_file(args.filepath, dry_run=not args.clean)

    if result.get('success'):
        print(f"\n" + "=" * 40)
        colored_print("RESULT: ", 1)
        colored_print_info_type(f"File: ", 1, f"{result['filename']}")
        colored_print_info_type(f"Total subtitles: ", 1,
                                f"{result['subtitle_count']}")
        print(f"Phony subtitles found: {result['phony_count']}")
        if args.clean and result['phony_count'] > 0:
            print("File has been cleaned!")
            if result.get('cleaned_file'):
                cleaned_filename = os.path.basename(result['cleaned_file'])
                print(f"New cleaned file created: {cleaned_filename}")

    else:
        print("Result:")
        print(result)
        print(
            f"\nFailed to process file: {result.get('error', 'Unknown error')}")
        exit(1)

"""

Example usage:

bash# 
Dry run - shows what would be cleaned but doesn't create new file

python script.py my-input-srt-file.srt

# Actually clean: creates my-input-srt-file-cleaned.srt

python script.py my-input-srt-file.srt --clean

Output example:

Processing: my-input-srt-file.srt
  - Parsed 245 subtitles
  - Found 2 PHONY subtitle(s):
    #1: Sous-titrage ST' 501
    #156: sous-titrage par Amara.org - merci de nous soutenir...

Found 2 phony subtitle(s) in my-input-srt-file.srt:
  - #1: Sous-titrage ST' 501...
  - #156: sous-titrage par Amara.org - merci de nous sout...
  → Cleaned file saved: my-input-srt-file-cleaned.srt

========================================

RESULT:

File: my-input-srt-file-cleaned.srt
Total subtitles: 243
Phony subtitles found: 2
File has been cleaned!

New cleaned file created: my-input-srt-file-cleaned.srt
"""

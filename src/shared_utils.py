# shared_utils.py


def remove_srt_extension(base_name):
    return base_name[:-4]


def make_cleaned_srt_filename(base_name):
    if "-input" in base_name:
        return swap(base_name)
    return f"{base_name} - cleaned.srt"


def swap(base_name):
    good_part = base_name.split("-input")[0]
    return good_part + " - cleaned.srt"


empty_log_ending = " - empty_log.txt"

filled_log_ending = " - cleaner_log.txt"


def make_empty_log_filename(base):
    return base + empty_log_ending


def make_log_with_cleaned_lines(base):
    return base + filled_log_ending

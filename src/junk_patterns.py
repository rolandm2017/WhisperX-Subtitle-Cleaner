"""
Configurable patterns for detecting junk subtitles.
Users can modify this file for their language/use case.
"""

JUNK_PATTERNS = [
    # Can use patterns that vary somewhat
    r'sous.titrage.*st[\'"]?\s*\d+',  # "Sous-titrage ST' 501"
    r'sous.titrage.*par.*amara\.org',  # "sous-titrage par Amara.org"
    r'sous.titrage.*fr',  # "sous-titrage fr"
    r'sous.titrage.*fr.*\d{4}',  # "Sous-titrage FR 2021"

    # Can use target recurrent exact matches
    r"^Sous-titrage Société Radio-Canada$",
    r"^Sous-titrage MFP\.$",
    r"^Abonnez-vous!$",
    r"^Merci d'avoir regardé cette vidéo !$",
    r"^Merci à tous$"
]

# Add your own patterns here for other languages (or replace the entries entirely)

# JUNK_PATTERNS = [
#     r'pattern1',
#     r'pattern2',
# ]

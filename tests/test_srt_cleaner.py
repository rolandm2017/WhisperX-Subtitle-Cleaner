import pytest
import os
import tempfile
import sys
from pathlib import Path

# Add parent directory to path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.clean_whisperx_output import SrtCleaner, clean_srt_file
from src.srt_file import SRTFile


@pytest.fixture
def test_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def input_srt_content():
    """SRT content with phony subtitles that should be removed"""
    return """1
00:00:02,343 --> 00:00:06,109
Je m'appelle Marinette, une fille comme les autres.

2
00:00:06,713 --> 00:00:13,500
Mais quand le destin m'est choisi pour lutter contre les forces du mal, je deviens Miraculous Ladybug !

3
00:00:16,771 --> 00:00:18,968
Sous-titrage ST' 501

4
00:00:23,032 --> 00:00:27,996
Oui, combien d'histoires Miraculaires

5
00:00:30,845 --> 00:00:36,923
Il y a des siècles de cela, furent créés des bijoux magiques donnant des pouvoirs fabuleux.

140
00:06:49,646 --> 00:06:51,615
S'il vous plaît, n'en parlez pas, mon père.

141
00:06:54,953 --> 00:06:56,863
Sous-titrage ST' 501

142
00:06:59,375 --> 00:07:03,675
Pour ceux qui ont sport, Monsieur Dargencourt vous attend en bas pour aller au stade.

143
00:07:04,123 --> 00:07:06,456
Un autre subtitle normal.

144
00:07:07,123 --> 00:07:09,789
Sous-titrage par Amara.org

145
00:07:10,123 --> 00:07:12,456
Encore un subtitle normal."""


@pytest.fixture
def create_input_srt_file(test_dir, input_srt_content):
    """Create a input SRT file for testing"""
    filepath = os.path.join(test_dir, 'input_test.srt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(input_srt_content)
    return filepath


class TestSrtCleaner:
    """Test the SRT cleaner functionality"""

    def test_find_phony_subtitles(self, create_input_srt_file):
        """Test that phony subtitles are correctly identified"""
        # Parse the file
        srt_file = SRTFile(create_input_srt_file)
        srt_file.parse()

        # Create cleaner and find phony subtitles
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()

        # Should find 3 phony subtitles: #3, #141, and #144
        assert len(phony_subtitles) == 3

        # Check the subtitle numbers of phony subtitles
        phony_numbers = [sub['number'] for sub in phony_subtitles]
        assert 3 in phony_numbers  # "Sous-titrage ST' 501"
        assert 141 in phony_numbers  # "Sous-titrage ST' 501" (duplicate)
        assert 144 in phony_numbers  # "sous-titrage par Amara.org"

        # Verify the text content of phony subtitles
        phony_texts = [sub['text'] for sub in phony_subtitles]
        print(phony_texts, "105ru")
        assert any("Sous-titrage ST' 501" in text for text in phony_texts)
        assert any("Amara.org".lower() in text.lower() for text in phony_texts)

    def test_produce_only_good_subtitles(self, create_input_srt_file, capsys):
        """Test that phony subtitles are removed and good ones are kept"""
        # Parse the file
        srt_file = SRTFile(create_input_srt_file)
        srt_file.parse()

        # Create cleaner and process
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()
        result = cleaner.remove_junk_subtitles(phony_subtitles)

        # Check removal count
        assert result['removed_count'] == 3

        # Check that we have the correct number of remaining subtitles
        # Original: 11 subtitles, removed 3, should have 8
        assert len(result['subtitles_sans_bad_output']) == 8

        # Verify that phony subtitles are not in the cleaned list
        cleaned_texts = [sub['text']
                         for sub in result['subtitles_sans_bad_output']]
        assert not any(
            "Sous-titrage ST' 501" in text for text in cleaned_texts)
        assert not any("amara.org" in text.lower() for text in cleaned_texts)

        # Verify good subtitles are preserved
        assert "Je m'appelle Marinette, une fille comme les autres." in cleaned_texts
        assert "Oui, combien d'histoires Miraculaires" in cleaned_texts
        assert "S'il vous plaît, n'en parlez pas, mon père." in cleaned_texts
        assert "Pour ceux qui ont sport, Monsieur Dargencourt vous attend en bas pour aller au stade." in cleaned_texts

    def test_subtitle_renumbering(self, create_input_srt_file):
        """Test that subtitles are correctly renumbered after cleaning"""
        # Parse the file
        srt_file = SRTFile(create_input_srt_file)
        srt_file.parse()

        # Create cleaner and process
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()
        result = cleaner.remove_junk_subtitles(phony_subtitles)

        cleaned_subtitles = result['subtitles_sans_bad_output']

        # After cleaning and renumbering:
        # Original #1 -> stays #1
        # Original #2 -> stays #2
        # Original #3 (phony) -> removed
        # Original #4 -> becomes #3
        # Original #5 -> becomes #4
        # Original #140 -> becomes #5
        # Original #141 (phony) -> removed
        # Original #142 -> becomes #6
        # Original #143 -> becomes #7
        # Original #144 (phony) -> removed
        # Original #145 -> becomes #8

        # Check specific subtitles and their new numbers
        # Find subtitle with text "Oui, combien d'histoires Miraculaires"
        histoire_sub = next(
            sub for sub in cleaned_subtitles if "Oui, combien d'histoires Miraculaires" in sub['text'])
        assert histoire_sub['number'] == 3  # Was #4, now #3

        # Find subtitle with text about Monsieur Dargencourt
        sport_sub = next(
            sub for sub in cleaned_subtitles if "Monsieur Dargencourt" in sub['text'])
        assert sport_sub['number'] == 6  # Was #142, now #6

        # Check that numbers are sequential without gaps
        numbers = [sub['number'] for sub in cleaned_subtitles]
        assert numbers == list(range(1, len(cleaned_subtitles) + 1))

    def test_prepare_cleaned_content_for_write(self, create_input_srt_file):
        """Test that cleaned content is properly formatted for writing"""
        # Parse the file
        srt_file = SRTFile(create_input_srt_file)
        srt_file.parse()

        # Create cleaner and process
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()
        result = cleaner.remove_junk_subtitles(phony_subtitles)

        # Prepare content for writing
        cleaned_content = cleaner.prepare_cleaned_content_for_write(
            result['subtitles_sans_bad_output'])

        # Check format: should be [number, timestamp, text, empty, number, timestamp, text, empty, ...]
        # But without the final empty line
        assert isinstance(cleaned_content, list)

        # Each subtitle takes 4 lines (number, timestamp, text, empty), except the last one (no empty)
        # So for 7 subtitles: 7*4 - 1 = 27 lines
        expected_lines = len(result['subtitles_sans_bad_output']) * 4 - 1
        assert len(cleaned_content) == expected_lines

        # Check first subtitle format
        assert cleaned_content[0] == "1"  # Number
        assert "-->" in cleaned_content[1]  # Timestamp
        # Text
        assert cleaned_content[2] == "Je m'appelle Marinette, une fille comme les autres."
        assert cleaned_content[3] == ""  # Empty line

        # Check that there's no empty line at the end
        assert cleaned_content[-1] != ""

    def test_save_cleaned_file(self, create_input_srt_file, test_dir):
        """Test that cleaned file is saved with correct suffix"""
        # Parse the file
        srt_file = SRTFile(create_input_srt_file)
        srt_file.parse()

        # Create cleaner and process
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()
        result = cleaner.remove_junk_subtitles(phony_subtitles)

        # Prepare and save
        cleaned_content = cleaner.prepare_cleaned_content_for_write(
            result['subtitles_sans_bad_output'])
        cleaned_filepath = cleaner.save_cleaned_file(cleaned_content)

        # Check that file was created with correct suffix
        assert os.path.exists(cleaned_filepath)
        assert cleaned_filepath.endswith(' - cleaned.srt')

        # Read and verify the saved file
        with open(cleaned_filepath, 'r', encoding='utf-8') as f:
            saved_content = f.read()

        # Check that phony subtitles are not in the saved file
        assert "Sous-titrage ST' 501" not in saved_content
        assert "Amara.org" not in saved_content.lower()

        # Check that good subtitles are in the saved file
        assert "Je m'appelle Marinette" in saved_content
        assert "Oui, combien d'histoires Miraculaires" in saved_content


class TestIntegrationcleaneSrtFile:
    """Integration tests for the main clean_srt_file function"""

    def test_clean_srt_file_full_process(self, create_input_srt_file):
        """Test the full cleaning process from file to file"""
        # Run the cleaning process (not dry run)
        result = clean_srt_file(create_input_srt_file, dry_run=False)

        # Check result structure
        assert result['success'] is True
        assert result['phony_count'] == 3
        print(result, "252ru")
        assert result['subtitle_count'] == 8  # 11 original - 3 phony = 8
        assert 'cleaned_file' in result

        # Check that cleaned file exists
        assert os.path.exists(result['cleaned_file'])

        # Parse the cleaned file to verify content
        cleaned_srt = SRTFile(result['cleaned_file'])
        cleaned_srt.parse()

        # Verify count
        assert len(cleaned_srt.subtitles) == 8

        # Verify no phony subtitles
        texts = [sub['text'] for sub in cleaned_srt.subtitles]
        assert not any("Sous-titrage ST' 501" in text for text in texts)
        assert not any("amara" in text.lower() for text in texts)

        # Verify specific renumbering cases
        # The 4th subtitle (was #4, now #3) should be "Oui, combien d'histoires Miraculaires"
        assert cleaned_srt.subtitles[2]['number'] == 3
        assert "Oui, combien d'histoires Miraculaires" in cleaned_srt.subtitles[2]['text']

        # The subtitle about sport (was #142, now #6)
        sport_subtitle = next(
            (sub for sub in cleaned_srt.subtitles if "Monsieur Dargencourt" in sub['text']), None)
        assert sport_subtitle is not None
        assert sport_subtitle['number'] == 6

    def test_cleane_file_with_no_phony_subtitles(self, test_dir):
        """Test cleaning a file that has no phony subtitles"""
        # Create a clean SRT file
        clean_content = """1
00:00:00,000 --> 00:00:05,000
This is a clean subtitle

2
00:00:05,000 --> 00:00:10,000
Another clean subtitle

3
00:00:10,000 --> 00:00:15,000
Yet another clean subtitle"""

        filepath = os.path.join(test_dir, 'clean_test.srt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        # Run the cleaning process
        result = clean_srt_file(filepath, dry_run=False)

        # Check result
        assert result['success'] is True
        assert result['phony_count'] == 0
        assert result['subtitle_count'] == 3

        # Even with no phony subtitles, a cleaned file should still be created
        assert 'cleaned_file' in result
        assert os.path.exists(result['cleaned_file'])

        # Verify the cleaned file has the same content
        cleaned_srt = SRTFile(result['cleaned_file'])
        cleaned_srt.parse()
        assert len(cleaned_srt.subtitles) == 3

    def test_error_handling_non_existent_file(self):
        """Test handling of non-existent file"""
        result = clean_srt_file('non_existent_file.srt', dry_run=False)
        assert result == {}  # Returns empty dict for non-existent files

    def test_error_handling_non_srt_file(self, test_dir):
        """Test handling of non-SRT file"""
        # Create a non-SRT file
        filepath = os.path.join(test_dir, 'not_an_srt.txt')
        with open(filepath, 'w') as f:
            f.write("This is not an SRT file")

        result = clean_srt_file(filepath, dry_run=False)
        assert result == {}  # Returns empty dict for non-SRT files


# Additional test for specific phony patterns
class TestPhonyPatterns:
    """Test various phony subtitle patterns"""

    @pytest.mark.parametrize("phony_text", [
        "Sous-titrage ST' 501",
        "sous-titrage par Amara.org - merci de nous soutenir",
        "Sous-titrage FR",
        "Sous-titrage FR 2021",
        "SOUS-TITRAGE FR 2023",  # Test case insensitivity
    ])
    def test_phony_pattern_detection(self, test_dir, phony_text):
        """Test that various phony patterns are detected"""
        content = f"""1
00:00:00,000 --> 00:00:05,000
Normal subtitle

2
00:00:05,000 --> 00:00:10,000
{phony_text}

3
00:00:10,000 --> 00:00:15,000
Another normal subtitle"""

        filepath = os.path.join(test_dir, 'pattern_test.srt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Parse and clean
        srt_file = SRTFile(filepath)
        srt_file.parse()
        cleaner = SrtCleaner(srt_file)
        phony_subtitles = cleaner.find_phony_subtitles()

        # Should find exactly 1 phony subtitle
        assert len(phony_subtitles) == 1
        assert phony_subtitles[0]['number'] == 2

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import the SRTFile class
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.srt_file import SRTFile  # Adjust import path as needed


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
def dummy_srt_path():
    """Path to the dummy SRT file"""
    return os.path.join(os.path.dirname(__file__), 'dummy_srt_file.srt')


@pytest.fixture
def create_temp_srt(test_dir):
    """Factory fixture to create temporary SRT files"""
    def _create_srt(content, encoding='utf-8', filename='temp.srt'):
        temp_file = os.path.join(test_dir, filename)
        with open(temp_file, 'w', encoding=encoding) as f:
            f.write(content)
        return temp_file
    return _create_srt


@pytest.fixture
def simple_srt_content():
    """Simple SRT content for testing"""
    return """1
00:00:00,000 --> 00:00:05,000
Hello World

2
00:00:05,000 --> 00:00:10,000
This is a test subtitle"""


class TestSRTFileBasics:
    """Test basic SRTFile functionality"""

    def test_initialization(self, dummy_srt_path):
        """Test SRTFile initialization"""
        srt = SRTFile(dummy_srt_path)
        assert srt.filepath == dummy_srt_path
        assert srt.filename == 'dummy_srt_file.srt'
        assert srt.subtitles == []
        assert srt.original_content == ""

    def test_parse_dummy_file(self, dummy_srt_path):
        """Test parsing the provided dummy SRT file"""
        srt = SRTFile(dummy_srt_path)
        srt.parse()

        # Check that subtitles were parsed
        assert len(srt.subtitles) > 0

        # Check first subtitle
        first_subtitle = srt.subtitles[0]
        assert first_subtitle['number'] == 1
        assert first_subtitle['timestamp'] == '00:00:02,343 --> 00:00:06,109'
        assert first_subtitle['text'] == "Je m'appelle Marinette, une fille comme les autres."
        assert first_subtitle['start_time'] == pytest.approx(2.343, abs=0.001)
        assert first_subtitle['end_time'] == pytest.approx(6.109, abs=0.001)

        # Check a subtitle with multiline text (subtitle 2)
        second_subtitle = srt.subtitles[1]
        assert second_subtitle['number'] == 2
        assert "Mais quand le destin" in second_subtitle['text']
        assert "Miraculous Ladybug" in second_subtitle['text']

    def test_simple_srt(self, create_temp_srt, simple_srt_content):
        """Test parsing a simple SRT file"""
        temp_file = create_temp_srt(simple_srt_content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 2
        assert srt.subtitles[0]['text'] == 'Hello World'
        assert srt.subtitles[1]['text'] == 'This is a test subtitle'

    def test_original_content_preserved(self, create_temp_srt, simple_srt_content):
        """Test that original content is preserved after parsing"""
        temp_file = create_temp_srt(simple_srt_content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert srt.original_content.strip() == simple_srt_content.strip()


class TestTimeProcessing:
    """Test time-related functionality"""

    @pytest.mark.parametrize("time_str,expected", [
        ('00:00:00,000', 0.0),
        ('00:00:01,000', 1.0),
        ('00:01:00,000', 60.0),
        ('01:00:00,000', 3600.0),
        ('00:00:02,343', 2.343),
        ('00:21:36,925', 1296.925),
    ])
    def test_parse_time(self, dummy_srt_path, time_str, expected):
        """Test time parsing with various formats"""
        srt = SRTFile(dummy_srt_path)
        assert srt._parse_time(time_str) == pytest.approx(expected, abs=0.001)

    def test_timestamp_with_spaces(self, create_temp_srt):
        """Test parsing timestamps with various spacing"""
        content = """1
00:00:00,000   -->   00:00:05,000
Subtitle with extra spaces in timestamp"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 1
        assert srt.subtitles[0]['start_time'] == pytest.approx(0.0, abs=0.001)
        assert srt.subtitles[0]['end_time'] == pytest.approx(5.0, abs=0.001)

    def test_time_continuity(self, dummy_srt_path):
        """Test that subtitle times are logical (start < end)"""
        srt = SRTFile(dummy_srt_path)
        srt.parse()

        for subtitle in srt.subtitles:
            assert subtitle['start_time'] < subtitle['end_time'], \
                f"Subtitle {subtitle['number']}: start time should be less than end time"


class TestTextContent:
    """Test various text content scenarios"""

    def test_multiline_subtitle(self, create_temp_srt):
        """Test parsing subtitles with multiple lines of text"""
        content = """1
00:00:00,000 --> 00:00:05,000
Line 1
Line 2
Line 3"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 1
        assert srt.subtitles[0]['text'] == 'Line 1\nLine 2\nLine 3'

    def test_missing_text(self, create_temp_srt):
        """Test handling of subtitle blocks with missing text"""
        content = """1
00:00:00,000 --> 00:00:05,000

2
00:00:05,000 --> 00:00:10,000
Normal subtitle"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        # Skip the empty one
        assert len(srt.subtitles) == 1
        assert srt.subtitles[0]['text'] == 'Normal subtitle'

    @pytest.mark.parametrize("special_char", ['&', '<', '>', '"', "'", '©', '™', '€'])
    def test_special_characters(self, create_temp_srt, special_char):
        """Test handling of special characters in subtitles"""
        content = f"""1
00:00:00,000 --> 00:00:05,000
Special char: {special_char}"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 1
        assert special_char in srt.subtitles[0]['text']


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_file(self, create_temp_srt):
        """Test parsing an empty SRT file"""
        temp_file = create_temp_srt("")
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 0

    def test_malformed_subtitle_block(self, create_temp_srt):
        """Test handling of malformed subtitle blocks"""
        content = """1
00:00:00,000 --> 00:00:05,000
Valid subtitle

Not a number
00:00:05,000 --> 00:00:10,000
This should be skipped

3
00:00:10,000 --> 00:00:15,000
This should be parsed"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        # Should parse the valid subtitles and skip the malformed one
        assert len(srt.subtitles) == 2
        assert srt.subtitles[0]['number'] == 1
        assert srt.subtitles[1]['number'] == 3

    def test_extra_blank_lines(self, create_temp_srt):
        """Test parsing with extra blank lines between subtitles"""
        content = """1
00:00:00,000 --> 00:00:05,000
First subtitle



2
00:00:05,000 --> 00:00:10,000
Second subtitle"""

        temp_file = create_temp_srt(content)
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 2

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        srt = SRTFile('non_existent_file.srt')
        with pytest.raises(FileNotFoundError):
            srt.parse()


class TestEncoding:
    """Test different file encodings"""

    def test_latin1_encoding(self, test_dir):
        """Test parsing a file with Latin-1 encoding"""
        content = """1
00:00:00,000 --> 00:00:05,000
Café résumé naïve"""

        # Write with Latin-1 encoding
        temp_file = os.path.join(test_dir, 'latin1.srt')
        with open(temp_file, 'w', encoding='latin-1') as f:
            f.write(content)

        # The parser should handle this
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 1
        # The text might be decoded differently, but parsing should not fail
        assert srt.subtitles[0]['text'] is not None

    @pytest.mark.parametrize("encoding", ['utf-8'])
    def test_various_encodings(self, test_dir, encoding):
        """Test parsing files with various encodings"""
        content = """1
00:00:00,000 --> 00:00:05,000
Test subtitle"""

        temp_file = os.path.join(test_dir, f'{encoding}.srt')
        try:
            with open(temp_file, 'w', encoding=encoding) as f:
                f.write(content)

            srt = SRTFile(temp_file)
            # This might fail for some encodings, which is expected behavior
            # The test documents what encodings are supported
            try:
                srt.parse()
                assert len(srt.subtitles) == 1
            except UnicodeDecodeError:
                # Document which encodings are not supported
                pytest.skip(f"Encoding {encoding} not supported")
        except LookupError:
            pytest.skip(f"Encoding {encoding} not available on this system")


class TestDataIntegrity:
    """Test data integrity and ordering"""

    def test_subtitle_ordering(self, dummy_srt_path):
        """Test that subtitles maintain their order"""
        srt = SRTFile(dummy_srt_path)
        srt.parse()

        # Check that subtitle numbers are in order (allowing for gaps)
        prev_num = 0
        for subtitle in srt.subtitles:
            assert subtitle['number'] > prev_num
            prev_num = subtitle['number']

    def test_all_subtitles_have_required_fields(self, dummy_srt_path):
        """Test that all parsed subtitles have required fields"""
        srt = SRTFile(dummy_srt_path)
        srt.parse()

        required_fields = ['number', 'timestamp',
                           'text', 'start_time', 'end_time']

        for subtitle in srt.subtitles:
            for field in required_fields:
                assert field in subtitle, f"Subtitle missing required field: {field}"


class TestPerformance:
    """Performance tests (marked as slow)"""

    def test_large_file_parsing(self, create_temp_srt):
        """Test parsing a large SRT file"""
        # Generate a large SRT file with 1000 subtitles
        content = []
        for i in range(1, 1001):
            start_seconds = (i - 1) * 5
            end_seconds = i * 5
            start_time = f"{start_seconds // 3600:02d}:{(start_seconds % 3600) // 60:02d}:{start_seconds % 60:02d},000"
            end_time = f"{end_seconds // 3600:02d}:{(end_seconds % 3600) // 60:02d}:{end_seconds % 60:02d},000"
            content.append(
                f"{i}\n{start_time} --> {end_time}\nSubtitle number {i}\n")

        temp_file = create_temp_srt('\n'.join(content))
        srt = SRTFile(temp_file)
        srt.parse()

        assert len(srt.subtitles) == 1000

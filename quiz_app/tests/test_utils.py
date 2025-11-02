import os
import pytest

from quiz_app.api import utils


@pytest.mark.django_db
def test_download_audio(monkeypatch, tmp_path):
    """
    Testet download_audio, ohne wirklich was aus dem Internet zu laden.
    Wir mocken NUR das, was in utils.py benutzt wird.
    """

    # 1) output_dir auf tmp_path umbiegen
    #    In utils.py steht: os.path.join("quiz_app", "audio_file")
    #    Wir sagen: immer wenn utils os.path.join(...) aufruft,
    #    soll ein Pfad UNTER tmp_path rauskommen.
    def fake_join(*parts):
        # Beispiel-Aufrufe in utils:
        # - os.path.join("quiz_app", "audio_file")
        # - os.path.join(output_dir, "%(title)s.%(ext)s")
        if parts[0] == "quiz_app":
            # -> /tmp/.../audio_file
            return str(tmp_path / "audio_file")
        # alle anderen joins machen wir ganz simpel selber
        return "/".join(str(p) for p in parts)

    # WICHTIG: nur im utils-Modul patchen, nicht global!
    monkeypatch.setattr(utils.os.path, "join", fake_join)

    # 2) Verzeichnis-Erstellung stilllegen
    monkeypatch.setattr(utils.os, "makedirs", lambda *a, **k: None)

    # 3) Fake YoutubeDL
    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=True):
            # so tun als ob
            return {"title": "Mein Video", "ext": "webm"}

        def prepare_filename(self, info):
            # das wäre die Datei, die yt_dlp "runtergeladen" hätte
            return str(tmp_path / "audio_file" / "Mein Video.webm")

    monkeypatch.setattr(utils.yt_dlp, "YoutubeDL", FakeYDL)

    # 4) exists: wir sagen „ja, die mp3 gibt es“
    def fake_exists(path):
        # wir behaupten einfach: alle Pfade existieren
        return True

    monkeypatch.setattr(utils.os.path, "exists", fake_exists)

    # 5) os.replace mocken (wird evtl. aufgerufen)
    monkeypatch.setattr(utils.os, "replace", lambda *a, **k: None)

    # 6) Call!
    result = utils.download_audio("https://www.youtube.com/watch?v=abc123")

    assert result.endswith(".mp3")
    # und optional:
    assert "audio_file" in result

@pytest.mark.parametrize(
    "url, expected",
    [
        # standard full URL with only v=
        ("https://www.youtube.com/watch?v=abc123DEF45", "abc123DEF45"),
        # full URL with extra params after id
        ("https://www.youtube.com/watch?v=abc123DEF45&list=PL", "abc123DEF45"),
        # short youtu.be link with valid-length id
        ("https://youtu.be/abc123DEF45", "abc123DEF45"),
        # short link with mixed allowed chars
        ("http://youtu.be/ABC_def-0", "ABC_def-0"),
        # v= present anywhere (domain not checked by function) — still extracted
        ("https://example.com/watch?v=XYZxyz123", "XYZxyz123"),
    ],
)
def test_yt_url_to_id_valid(url, expected):
    assert utils.yt_url_to_id(url) == expected

@pytest.mark.parametrize(
    "url",
    [
        # short youtu.be but id too short (<6) → regex should not match
        "https://youtu.be/abc",
        # no v= and no youtu.be pattern
        "https://www.youtube.com/",
        "https://example.com/",
        "",  # empty string
    ],
)
def test_yt_url_to_id_invalid_strings(url):
    assert utils.yt_url_to_id(url) is None
    
@pytest.mark.parametrize("non_str", [None, 123, 12.34, [], {}])
def test_yt_url_to_id_non_string_returns_none(non_str):
    assert utils.yt_url_to_id(non_str) is None

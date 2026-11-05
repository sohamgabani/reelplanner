import pytest

from reelplanner import caption, db
from reelplanner.cli import main


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.add_page(c, "@brandbreakdown.lab", "brand breakdowns")
    yield c
    c.close()


def test_add_and_list_reel(conn):
    rid = db.add_reel(conn, "brandbreakdown.lab", "Why Nike wins", hook="Nike sells a feeling")
    rows = db.list_reels(conn)
    assert len(rows) == 1 and rows[0]["id"] == rid and rows[0]["status"] == "idea"


def test_unknown_page(conn):
    with pytest.raises(LookupError):
        db.add_reel(conn, "nope", "x")


def test_bad_status(conn):
    rid = db.add_reel(conn, "brandbreakdown.lab", "x")
    with pytest.raises(ValueError):
        db.update_reel(conn, rid, status="viral")


def test_filter_by_status(conn):
    a = db.add_reel(conn, "brandbreakdown.lab", "a")
    db.add_reel(conn, "brandbreakdown.lab", "b")
    db.update_reel(conn, a, status="posted")
    assert [r["title"] for r in db.list_reels(conn, status="posted")] == ["a"]


def test_caption_ok():
    assert caption.check("Short hook line\n\nBody text #brand #marketing") == []


def test_caption_problems():
    text = "x" * 200 + " — " + " ".join(f"#t{i}" for i in range(7)) + " #t1"
    problems = " ".join(caption.check(text))
    assert "first line" in problems
    assert "hashtags" in problems
    assert "repeated" in problems
    assert "em dash" in problems


def test_cli_flow(tmp_path, capsys):
    dbf = str(tmp_path / "r.db")
    assert main(["--db", dbf, "page", "add", "aisketched"]) == 0
    assert main(["--db", dbf, "add", "aisketched", "AI news", "--caption", "ok #ai"]) == 0
    assert main(["--db", dbf, "edit", "1", "--date", "2026-11-10"]) == 0
    assert main(["--db", dbf, "week", "--start", "2026-11-09"]) == 0
    assert "AI news" in capsys.readouterr().out
    assert main(["--db", dbf, "show", "99"]) == 2

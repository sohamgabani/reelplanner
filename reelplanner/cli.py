"""Command-line interface: `reelplanner <command> ...`"""

import argparse
import sys
from datetime import date, timedelta

from . import caption, db


def _print_reels(rows) -> None:
    if not rows:
        print("No reels found.")
        return
    for r in rows:
        when = r["post_date"] or "-"
        print(f"#{r['id']:<4} @{r['handle']:<22} {r['status']:<9} {when:<10}  {r['title']}")


def cmd_page_add(conn, a):
    db.add_page(conn, a.handle, a.niche or "")
    print(f"Added page @{a.handle.lstrip('@')}")


def cmd_page_list(conn, a):
    pages = db.list_pages(conn)
    if not pages:
        print("No pages yet. Add one with: reelplanner page add <handle>")
    for p in pages:
        print(f"@{p['handle']:<24} {p['niche']}")


def cmd_add(conn, a):
    reel_id = db.add_reel(conn, a.page, a.title, a.hook or "", a.caption or "")
    print(f"Added reel #{reel_id}")


def cmd_list(conn, a):
    _print_reels(db.list_reels(conn, a.page, a.status))


def cmd_show(conn, a):
    r = db.get_reel(conn, a.id)
    print(f"#{r['id']} @{r['handle']}  [{r['status']}]  post: {r['post_date'] or '-'}")
    print(f"Title:   {r['title']}")
    print(f"Hook:    {r['hook'] or '-'}")
    print(f"Caption: {r['caption'] or '-'}")


def cmd_edit(conn, a):
    db.update_reel(conn, a.id, title=a.title, hook=a.hook, caption=a.caption,
                   status=a.status, post_date=a.date)
    print(f"Updated reel #{a.id}")


def cmd_delete(conn, a):
    db.delete_reel(conn, a.id)
    print(f"Deleted reel #{a.id}")


def cmd_check(conn, a):
    text = db.get_reel(conn, a.id)["caption"]
    problems = caption.check(text)
    if not problems:
        print("Caption looks good.")
        return 0
    for p in problems:
        print(f"- {p}")
    return 1


def cmd_week(conn, a):
    start = date.fromisoformat(a.start) if a.start else date.today()
    end = start + timedelta(days=6)
    rows = [r for r in db.list_reels(conn, a.page)
            if r["post_date"] and start.isoformat() <= r["post_date"] <= end.isoformat()]
    print(f"Week {start} to {end}")
    _print_reels(rows)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reelplanner", description="Plan reels for your Instagram pages.")
    p.add_argument("--db", help="path to the database file")
    sub = p.add_subparsers(dest="command", required=True)

    page = sub.add_parser("page", help="manage pages").add_subparsers(dest="page_cmd", required=True)
    pa = page.add_parser("add", help="add a page")
    pa.add_argument("handle")
    pa.add_argument("--niche")
    pa.set_defaults(func=cmd_page_add)
    page.add_parser("list", help="list pages").set_defaults(func=cmd_page_list)

    s = sub.add_parser("add", help="add a reel idea")
    s.add_argument("page")
    s.add_argument("title")
    s.add_argument("--hook")
    s.add_argument("--caption")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("list", help="list reels")
    s.add_argument("--page")
    s.add_argument("--status", choices=db.STATUSES)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="show one reel")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("edit", help="change a reel")
    s.add_argument("id", type=int)
    s.add_argument("--title")
    s.add_argument("--hook")
    s.add_argument("--caption")
    s.add_argument("--status", choices=db.STATUSES)
    s.add_argument("--date", help="post date, YYYY-MM-DD")
    s.set_defaults(func=cmd_edit)

    s = sub.add_parser("delete", help="delete a reel")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_delete)

    s = sub.add_parser("check", help="check a reel's caption")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("week", help="show reels scheduled for a week")
    s.add_argument("--start", help="first day, YYYY-MM-DD (default: today)")
    s.add_argument("--page")
    s.set_defaults(func=cmd_week)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    conn = db.connect(args.db)
    try:
        return args.func(conn, args) or 0
    except (LookupError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except db.sqlite3.IntegrityError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

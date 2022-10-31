#
# To run:
#
# $ DRF_TOKEN=$DRF_TOKEN_JERRELL python3 ./rich-dashboard.py
#

import os
import time
from itertools import cycle

import requests
from rich import box
from rich.color import Color, parse_rgb_hex
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text


class Dashboard():

    def __init__(self, session):

        self.color_normal = Color.from_triplet(parse_rgb_hex("00ff00"))
        self.color_error = Color.from_triplet(parse_rgb_hex("ff0000"))

        if "DRF_TOKEN" not in os.environ:
            raise Exception("DRF_TOKEN not found in environment")
        self.DRF_TOKEN = os.environ["DRF_TOKEN"]

        self.console = Console()
        self.layout = Layout()
        self.session = session

        # Divide the "screen" in to three parts
        self.layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=3, name="status"),
        )
        # Divide the "main" layout in to "side" and "bookmarks"
        self.layout["main"].split_row(
            Layout(name="side"),
            Layout(name="bookmarks", ratio=2)
        )
        # Divide the "side" layout in to two
        self.layout["side"].split(Layout(name="todo"), Layout(name="stats"))

        color = Color.from_triplet(parse_rgb_hex("ffa500"))
        text = Text(justify="center", style=Style(color=color, bold=True))
        text.append("Bordercore Operations Console")
        self.layout["header"].update(Panel(
            text,
            title=Text("Bordercore")
        ))

        self.layout["bookmarks"].update(Panel("Recent bookmarks", title="Bookmarks"))

    def update_status(self, status, error=False):

        if error:
            color = self.color_error
        else:
            color = self.color_normal

        self.layout["status"].update(
            Panel(
                Text(status, justify="center", style=Style(color=color)),
                title=Text("Status")
            )
        )

    def update_bookmarks(self):
        headers = {"Authorization": f"Token {self.DRF_TOKEN}"}
        r = session.get("https://www.bordercore.com/api/bookmarks/?ordering=-created", headers=headers)

        if r.status_code != 200:
            raise Exception(f"Error when accessing Bordercore REST API: status code={r.status_code}")

        info = r.json()
        colors = cycle(
            [
                Color.from_triplet(parse_rgb_hex("11ff00")),
                Color.from_triplet(parse_rgb_hex("56b04f"))
            ]
        )
        text = Text()

        for bookmark in info["results"]:
            text.append(bookmark["name"] + "\n", style=Style(color=next(colors)))
            self.layout["bookmarks"].update(Panel(
                text,
                title=Text("Bookmarks")
            ))

    def update_todos(self):
        headers = {"Authorization": f"Token {self.DRF_TOKEN}"}
        r = session.get("https://www.bordercore.com/api/todos/?priority=1", headers=headers)

        if r.status_code != 200:
            raise Exception(f"Error when accessing Bordercore REST API: status code={r.status_code}")

        info = r.json()
        colors = cycle(
            [
                Color.from_rgb(0, 136, 255),
                Color.from_rgb(73, 131, 182)
            ]
        )
        text = Text()

        for todo in info["results"]:
            text.append("• " + todo["name"] + "\n", style=Style(color=next(colors)))
            self.layout["todo"].update(Panel(
                text,
                title=Text("Todo Items")
            ))

    def update_stats(self):
        headers = {"Authorization": f"Token {self.DRF_TOKEN}"}
        r = session.get("https://www.bordercore.com/api/site/stats", headers=headers)

        if r.status_code != 200:
            raise Exception(f"Error when accessing Bordercore REST API: status code={r.status_code}")

        info = r.json()
        colors = cycle(
            [
                Color.from_rgb(168, 0, 146),
                Color.from_rgb(184, 40, 165)
            ]
        )

        table = Table(
            box=box.SIMPLE,
            style=Style(color=Color.from_rgb(184, 40, 165)),
            header_style=Style(color=next(colors)),
        )
        table.add_column("Name", justify="left", style=Style(color=Color.from_triplet(parse_rgb_hex("ee91e0"))))
        table.add_column("Value", style=Style(color=Color.from_triplet(parse_rgb_hex("9a488e"))))
        table.add_row("Untagged Bookmarks", f"{info['untagged_bookmarks']}")
        table.add_row("Drill For Review", f"{info['drill_needing_review']['count']}")

        self.layout["stats"].update(Panel(
            table,
            title=Text("Site Stats")
        ))


if __name__ == "__main__":

    session = requests.Session()

    # Ignore .netrc files. Useful for local debugging.
    session.trust_env = False

    dash = Dashboard(session=session)
    dash.update_bookmarks()

    with Live(dash.layout, screen=True):
        while True:
            try:
                dash.update_bookmarks()
                dash.update_todos()
                dash.update_stats()
                dash.update_status("All subsystems normal")
            except Exception as e:
                dash.update_status(str(e), error=True)
            time.sleep(10)

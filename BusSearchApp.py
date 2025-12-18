import wx
import wx.adv
import csv
from datetime import datetime

CSV_PATH = "karnataka_bus_10cities.csv"

# Load bus data
def load_buses(path):
    buses = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            buses.append(row)
    return buses

def parse_time(t):
    try:
        return datetime.strptime(t.strip(), "%I:%M %p").time()
    except:
        return datetime.strptime("12:00 AM", "%I:%M %p").time()

def parse_duration(d):
    try:
        parts = d.strip().split()
        h = int(parts[0].replace("h", ""))
        m = int(parts[1].replace("m", ""))
        return h * 60 + m
    except:
        return 10**6

class BusSearchApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Karnataka Bus Search ", size=(1180, 780))

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))  # pure white theme

        self.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        self.buses = load_buses(CSV_PATH)
        self.sources = sorted({b.get("Departure", "") for b in self.buses})
        self.destinations = sorted({b.get("Destination", "") for b in self.buses})
        ops = sorted({b.get("Bus Name", "") for b in self.buses if b.get("Bus Name")})
        self.operators = ["All Operators"] + ops

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ---------------------------
        # ROUTE FILTER SECTION
        # ---------------------------
        route_label = wx.StaticText(panel, label="ROUTE FILTERS")
        route_label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(route_label, flag=wx.LEFT | wx.TOP, border=20)

        main_sizer.Add(self.separator(panel), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

        route_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.src_combo = self.labeled_dropdown(panel, route_sizer, "Source", self.sources)
        self.dst_combo = self.labeled_dropdown(panel, route_sizer, "Destination", self.destinations)
        self.date_picker = self.labeled_date(panel, route_sizer, "Date")

        main_sizer.Add(route_sizer, flag=wx.LEFT | wx.TOP, border=20)

        # ---------------------------
        # BUS OPTIONS SECTION
        # ---------------------------
        options_label = wx.StaticText(panel, label="BUS OPTIONS")
        options_label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(options_label, flag=wx.LEFT | wx.TOP, border=20)

        main_sizer.Add(self.separator(panel), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

        opt_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ac_check = wx.CheckBox(panel, label="AC Only")
        self.sleeper_check = wx.CheckBox(panel, label="Sleeper Only")

        opt_sizer.Add(self.ac_check, flag=wx.LEFT | wx.TOP, border=20)
        opt_sizer.Add(self.sleeper_check, flag=wx.LEFT | wx.TOP, border=20)

        self.min_rating = self.labeled_text(panel, opt_sizer, "Min Rating", width=60)
        self.max_fare = self.labeled_text(panel, opt_sizer, "Max Fare", width=80)

        self.sort_choice = self.labeled_dropdown(panel, opt_sizer, "Sort By", [
            "Fare (Low → High)",
            "Timing (Earliest First)",
            "Rating (High → Low)",
            "Duration (Shortest First)"
        ])

        main_sizer.Add(opt_sizer, flag=wx.LEFT | wx.TOP, border=20)

        # ---------------------------
        # ACTIONS SECTION
        # ---------------------------
        actions_label = wx.StaticText(panel, label="ACTIONS")
        actions_label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(actions_label, flag=wx.LEFT | wx.TOP, border=20)

        main_sizer.Add(self.separator(panel), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

        action_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.search_btn = self.flat_button(panel, "Search", self.on_search)
        self.swap_btn = self.flat_button(panel, "Swap", self.on_swap)
        self.cheapest_btn = self.flat_button(panel, "Cheapest", self.on_cheapest)
        self.fastest_btn = self.flat_button(panel, "Fastest", self.on_fastest)

        action_sizer.Add(self.search_btn, flag=wx.LEFT | wx.TOP, border=20)
        action_sizer.Add(self.swap_btn, flag=wx.LEFT | wx.TOP, border=10)
        action_sizer.Add(self.cheapest_btn, flag=wx.LEFT | wx.TOP, border=10)
        action_sizer.Add(self.fastest_btn, flag=wx.LEFT | wx.TOP, border=10)

        main_sizer.Add(action_sizer)

        # ---------------------------
        # RESULTS TABLE
        # ---------------------------
        self.table = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        cols = [
            "Bus Number", "Operator", "Timing", "Fare (INR)",
            "Ratings", "Duration", "AC", "Sleeper",
            "Seats", "From", "To"
        ]

        for i, c in enumerate(cols):
            self.table.InsertColumn(i, c, width=110)

        self.table.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

        main_sizer.Add(self.table, proportion=1, flag=wx.EXPAND | wx.ALL, border=20)

        self.filtered = []
        panel.SetSizer(main_sizer)
        self.Center()
        self.Show()

    # ---------------------------
    # UI HELPERS
    # ---------------------------
    def separator(self, parent):
        line = wx.StaticLine(parent, style=wx.LI_HORIZONTAL)
        line.SetBackgroundColour(wx.Colour(220, 220, 220))
        return line

    def flat_button(self, parent, label, handler):
        btn = wx.Button(parent, label=label, style=wx.BORDER_NONE)
        btn.SetBackgroundColour(wx.Colour(245, 245, 245))
        btn.SetForegroundColour(wx.Colour(30, 30, 30))
        btn.Bind(wx.EVT_BUTTON, handler)
        return btn

    def labeled_dropdown(self, parent, sizer, label, choices):
        box = wx.BoxSizer(wx.VERTICAL)
        lab = wx.StaticText(parent, label=label)
        dd = wx.ComboBox(parent, choices=choices, style=wx.CB_READONLY, size=(200, -1))
        box.Add(lab)
        box.Add(dd, flag=wx.TOP, border=5)
        sizer.Add(box, flag=wx.LEFT, border=20)
        return dd

    def labeled_date(self, parent, sizer, label):
        box = wx.BoxSizer(wx.VERTICAL)
        lab = wx.StaticText(parent, label=label)
        dp = wx.adv.DatePickerCtrl(parent)
        box.Add(lab)
        box.Add(dp, flag=wx.TOP, border=5)
        sizer.Add(box, flag=wx.LEFT, border=20)
        return dp

    def labeled_text(self, parent, sizer, label, width):
        box = wx.BoxSizer(wx.VERTICAL)
        lab = wx.StaticText(parent, label=label)
        tc = wx.TextCtrl(parent, size=(width, -1))
        box.Add(lab)
        box.Add(tc, flag=wx.TOP, border=5)
        sizer.Add(box, flag=wx.LEFT, border=20)
        return tc

    # ---------------------------
    # SEARCH LOGIC
    # ---------------------------
    def get_selected_date_iso(self):
        return self.date_picker.GetValue().FormatISODate()

    def on_search(self, evt):
        src = self.src_combo.GetValue().strip().lower()
        dst = self.dst_combo.GetValue().strip().lower()
        date_iso = self.get_selected_date_iso()

        try:
            weekday = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%A")
        except:
            weekday = ""

        ac_only = self.ac_check.GetValue()
        sleeper_only = self.sleeper_check.GetValue()

        min_rating = self.min_rating.GetValue().strip()
        max_fare = self.max_fare.GetValue().strip()

        sort_idx = self.sort_choice.GetSelection()

        results = []

        for b in self.buses:

            if src and b["Departure"].lower() != src:
                continue

            if dst and b["Destination"].lower() != dst:
                continue

            if weekday and weekday not in b["Day of Departure"]:
                continue

            if ac_only and b["AC"].lower() != "yes":
                continue

            if sleeper_only and b["Sleeper"].lower() != "yes":
                continue

            if min_rating:
                try:
                    if float(b["Ratings"]) < float(min_rating):
                        continue
                except:
                    continue

            if max_fare:
                try:
                    if int(b["Fare (INR)"]) > int(max_fare):
                        continue
                except:
                    continue

            results.append(b)

        # Sorting
        if sort_idx == 0:
            results.sort(key=lambda x: int(x["Fare (INR)"]))
        elif sort_idx == 1:
            results.sort(key=lambda x: parse_time(x["Timing"]))
        elif sort_idx == 2:
            results.sort(key=lambda x: float(x["Ratings"]), reverse=True)
        elif sort_idx == 3:
            results.sort(key=lambda x: parse_duration(x["Duration"]))

        self.filtered = results
        self.populate_table(results)

    def populate_table(self, results):
        self.table.DeleteAllItems()

        for b in results:
            idx = self.table.InsertItem(self.table.GetItemCount(), b["Bus Number"])
            self.table.SetItem(idx, 1, b["Bus Name"])
            self.table.SetItem(idx, 2, b["Timing"])
            self.table.SetItem(idx, 3, b["Fare (INR)"])

            # Ratings with warning
            rating = float(b["Ratings"])
            rating_label = f"{rating} ⚠" if rating < 3.0 else f"{rating}"
            self.table.SetItem(idx, 4, rating_label)

            self.table.SetItem(idx, 5, b["Duration"])
            self.table.SetItem(idx, 6, b["AC"])
            self.table.SetItem(idx, 7, b["Sleeper"])

            # Seats with warning
            seats = int(b["Seats"])
            seat_label = f"{seats} ⚠" if seats < 5 else str(seats)
            self.table.SetItem(idx, 8, seat_label)

            self.table.SetItem(idx, 9, b["Departure"])
            self.table.SetItem(idx, 10, b["Destination"])

    def on_item_activated(self, evt):
        idx = evt.GetIndex()
        busnum = self.table.GetItemText(idx)

        selected = None
        for b in self.filtered:
            if b["Bus Number"] == busnum:
                selected = b
                break

        if not selected:
            return

        dlg = wx.Dialog(self, title="Bus Details", size=(500, 500))
        panel = wx.Panel(dlg)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))

        text = "\n".join([
            f"Bus Number: {selected['Bus Number']}",
            f"Operator: {selected['Bus Name']}",
            f"Route: {selected['Departure']} → {selected['Destination']}",
            f"Timing: {selected['Timing']}",
            f"Duration: {selected['Duration']}",
            f"Fare: ₹{selected['Fare (INR)']}",
            f"Seats: {selected['Seats']}",
            f"AC: {selected['AC']}",
            f"Sleeper: {selected['Sleeper']}",
            f"Ratings: {selected['Ratings']}",
            f"Contact: {selected['Contact Details']}",
            f"Stops: {selected['In Between Stops']}",
            f"Features: {selected['Features']}",
            f"Remarks: {selected['Remarks']}",
        ])

        wx.StaticText(panel, label=text, pos=(20, 20))

        close_btn = wx.Button(panel, label="Close", pos=(200, 420))
        close_btn.Bind(wx.EVT_BUTTON, lambda e: dlg.Destroy())

        dlg.ShowModal()

    def on_swap(self, evt):
        src = self.src_combo.GetValue()
        dst = self.dst_combo.GetValue()
        self.src_combo.SetValue(dst)
        self.dst_combo.SetValue(src)
        self.on_search(None)

    def on_cheapest(self, evt):
        if not self.filtered:
            return
        cheapest = min(self.filtered, key=lambda x: int(x["Fare (INR)"]))
        self.populate_table([cheapest])
        self.filtered = [cheapest]

    def on_fastest(self, evt):
        if not self.filtered:
            return
        fastest = min(self.filtered, key=lambda x: parse_duration(x["Duration"]))
        self.populate_table([fastest])
        self.filtered = [fastest]


if __name__ == "__main__":
    app = wx.App(False)
    BusSearchApp()
    app.MainLoop()

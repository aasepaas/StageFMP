import customtkinter
import math


# ─────────────────────────────────────────────
#  Vaste afstanden (CROW-standaard placeholders)
# ─────────────────────────────────────────────
CROW_SPACING_M = 10.0         # onderlinge afstand kegels in meters
ROBOT_RADIUS   = 6            # visuele straal van robot-cirkel in canvas px


class PopupWindow:
    def __init__(self, master, callbackValues):
        self.master = master
        self.afterPopupCallback = callbackValues
        self.amountOfRobots = None
        self.optionformation = None

    def pop_up(self, listOfRobotNames=None):
        if listOfRobotNames is None:
            listOfRobotNames = [str(i) for i in range(1, 10)]
            self.amountOfRobots = 9
        else:
            self.amountOfRobots = len(listOfRobotNames)



        # ── state ──────────────────────────────────────────────────────────
        chosenSettings = {"Aantal": None, "Formatie": None, "RobotStart": "1"}

        popup = customtkinter.CTkToplevel(self.master)
        popup.title("Instellingen voor berekeningen")
        #popup.wm_maxsize(1300, 700)
        #popup.wm_minsize(600,600)
        popup.geometry("900x300")
        popup.wm_resizable(False, False)
        popup.wm_transient(self.master)
        popup.configure(fg_color="white")

        # ── lokale hulpfunctie ─────────────────────────────────────────────
        def _robot_index(robot_name: str, robot_list: list) -> int:
            try:
                return robot_list.index(robot_name)
            except ValueError:
                return 0

        # ── inner helpers ──────────────────────────────────────────────────
        def _redraw_preview(*_):
            """Herteken de canvas preview.

            Slot 0  = de huidige robot (altijd aanwezig, blauw).
            Slots 1..n_extra = de te berekenen extra kegels (oranje).
            """
            canvas.delete("all")

            aantal_val = chosenSettings["Aantal"]   # extra kegels (kan None zijn)
            robot_val  = chosenSettings["RobotStart"]

            # Huidige robot is altijd aanwezig; extra kegels optioneel in preview
            n_extra = int(aantal_val) if aantal_val is not None else 0
            n_total = 1 + n_extra   # robot + extra kegels

            road_y   = preview_h // 4
            margin_x = 30
            usable_w = preview_w - 2 * margin_x

            spacing_px = usable_w / max(n_total - 1, 1) if n_total > 1 else 0
            xs = [margin_x + i * spacing_px for i in range(n_total)]

            # ── wegbalk ───────────────────────────────────────────────────
            canvas.create_rectangle(
                0, road_y - 55, preview_w, road_y + 18,
                fill="#E8E4D9", outline="", tags="road",
            )
            canvas.create_line(
                0, road_y-45, preview_w, road_y-45,
                fill="white", width=4
            )

            # ── afstandslabel tussen eerste twee kegels ───────────────────
            if n_total > 1:
                x1, x2 = xs[0], xs[1]
                arr_y  = road_y - 32
                canvas.create_line(x1, arr_y, x2, arr_y, fill="#666", width=1,
                                   arrow="both", arrowshape=(5, 6, 3))
                canvas.create_text((x1 + x2) / 2, arr_y - 10,
                                   text=f"{CROW_SPACING_M:.1f} m",
                                   fill="#555", font=("Arial", 9))

            # ── kegels + labels ───────────────────────────────────────────
            for i, x in enumerate(xs):
                is_robot    = (i == 0)  # index 0 is altijd de huidige robot
                cone_color  = "#FF6B35" if not is_robot else "#2563EB"
                cone_stroke = "#CC4400" if not is_robot else "#1D4ED8"

                base_half = 9
                tip_y     = road_y - 26
                base_y    = road_y - 3

                # kegellichaam
                canvas.create_polygon(
                    x, tip_y,
                    x - base_half, base_y,
                    x + base_half, base_y,
                    fill=cone_color, outline=cone_stroke, width=1,
                )
                # reflectiestreep
                canvas.create_rectangle(
                    x - base_half + 2, base_y - 6,
                    x + base_half - 2, base_y - 3,
                    fill="white", outline="",
                )
                # basis
                canvas.create_rectangle(
                    x - base_half, base_y,
                    x + base_half, base_y + 3,
                    fill=cone_stroke, outline="",
                )

                # label boven kegel: robot = "R", extra = volgnummer
                label_y = tip_y - 13
                if is_robot:
                    canvas.create_text(x, label_y, text="R",
                                       fill=cone_color, font=("Arial", 9, "bold"))
                else:
                    canvas.create_text(x, label_y, text=str(i),
                                       fill=cone_color, font=("Arial", 9, "bold"))

                # robot-indicator onder de weg
                if is_robot:
                    ry = road_y + 36
                    canvas.create_oval(
                        x - ROBOT_RADIUS, ry - ROBOT_RADIUS,
                        x + ROBOT_RADIUS, ry + ROBOT_RADIUS,
                        fill="#2563EB", outline="#1D4ED8",
                    )
                    canvas.create_text(x, ry, text="R", fill="white",
                                       font=("Arial", 8, "bold"))
                    robot_label = robot_val if robot_val else "huidig"
                    canvas.create_text(x, ry + ROBOT_RADIUS + 10,
                                       text=robot_label,
                                       fill="#2563EB", font=("Arial", 8))

            # ── legenda ───────────────────────────────────────────────────
            leg_y = preview_h - 140
            # huidige robot
            canvas.create_oval(8, leg_y - 6, 20, leg_y + 6,
                               fill="#2563EB", outline="#1D4ED8")
            canvas.create_text(14, leg_y, text="R", anchor="center",
                               fill="white", font=("Arial", 7, "bold"))
            robot_label = robot_val if robot_val else "huidig"
            canvas.create_text(24, leg_y,
                               text=f"= {robot_label} (al geplaatst)",
                               anchor="w", fill="#444", font=("Arial", 9))
            # extra kegel
            canvas.create_rectangle(170, leg_y - 6, 182, leg_y + 6,
                                     fill="#FF6B35", outline="#CC4400")
            canvas.create_text(186, leg_y,
                               text=f"= te berekenen kegel ({n_extra}x)",
                               anchor="w", fill="#444", font=("Arial", 9))
            # totaal
            aantalTotaal = 1 + n_extra
            canvas.create_text(8, leg_y + 22,
                               text=f"Totaal aantal kegels: {aantalTotaal}",
                               anchor="w", fill="#111", font=("Arial", 11, "bold"))

            self.errorMsgAmountRobot = canvas.create_text(8, leg_y + 50,
                        text=f"Waarschuwing: {aantalTotaal} totale posities, maar alleen {self.amountOfRobots} kegelrobots online.",
                        anchor="w", fill="red", font=("Arial", 11, "bold"), state="hidden")

            self.errorMsgFormationAmountRobots = canvas.create_text(8, leg_y + 90,
                        text=f"Waarschuwing: kan geen CROW-formatie selecteren als \ntotaal aantal postities kleiner dan 5 is.",
                        anchor="w", fill="red", font=("Arial", 11, "bold"), state="hidden")


                        

        # ── callback helpers ───────────────────────────────────────────────
        def change_val(value):
            try:
                value = int(value)
                chosenSettings["Aantal"] = value
                _redraw_preview()
                if (int(value) + 1) > self.amountOfRobots:
                    canvas.itemconfig(self.errorMsgAmountRobot, state="normal")
                else:
                    canvas.itemconfig(self.errorMsgAmountRobot, state="hidden")
                    
            except Exception:
                pass
                
        def changeFormation(formation):
            try:
                if "CROW" in formation and ((chosenSettings["Aantal"] + 1) < 5):
                    canvas.itemconfig(self.errorMsgFormationAmountRobots, state="normal")
                    self.optionformation.set("Standaard 10m afstand")
                else:
                    canvas.itemconfig(self.errorMsgFormationAmountRobots, state="hidden")
            except:
                pass
            chosenSettings["Formatie"] = formation

        def changeStartRobot(robotName):
            chosenSettings["RobotStart"] = robotName
            _redraw_preview()

        def klaarKnopCommand():
            if any(val is None for val in chosenSettings.values()):
                print("Selecteer alle waarden voor het afsluiten.")
                return
            popup.destroy()
            self.afterPopupCallback(chosenSettings)

        # ── layout ─────────────────────────────────────────────────────────
        popup.grid_columnconfigure(0, weight=0)
        popup.grid_columnconfigure(1, weight=1)

        # ── opties-kolom ───────────────────────────────────────────────────
        options_frame = customtkinter.CTkFrame(popup, fg_color="transparent")
        options_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Aantal
        frame_amount = customtkinter.CTkFrame(options_frame)
        frame_amount.pack(fill="x", padx=0, pady=(0, 8))
        customtkinter.CTkLabel(
            frame_amount,
            text="Hoeveel extra kegels moeten er berekend worden:",
            anchor="w"
        ).grid(row=0, column=0, padx=10, pady=(6, 0), sticky="nw")
        customtkinter.CTkOptionMenu(
            frame_amount,
            values=[str(i) for i in range(1, 10)],
            command=change_val,
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nw")

        # Formatie
        frame_formation = customtkinter.CTkFrame(options_frame)
        frame_formation.pack(fill="x", padx=0, pady=(0, 8))
        customtkinter.CTkLabel(
            frame_formation,
            text="Welke formatie moet er toegepast worden:",
            anchor="w"
        ).grid(row=0, column=0, padx=10, pady=(6, 0), sticky="nw")
        self.optionformation = customtkinter.CTkOptionMenu(
            frame_formation,
            values=["Standaard 10m afstand", "CROW-formatie"],
            command=changeFormation,
        )
        self.optionformation.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nw")
        
        

        # # Robot
        # frame_robot = customtkinter.CTkFrame(options_frame)
        # frame_robot.pack(fill="x", padx=0, pady=(0, 8))
        # customtkinter.CTkLabel(
        #     frame_robot,
        #     text="Welke positie is de huidige kegelrobot:",
        #     anchor="w"
        # ).grid(row=0, column=0, padx=10, pady=(6, 0), sticky="nw")
        # customtkinter.CTkOptionMenu(
        #     frame_robot,
        #     values=[str(r) for r in listOfRobotNames],
        #     command=changeStartRobot,
        # ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nw")

        # Klaar-knop
        customtkinter.CTkButton(
            options_frame,
            text="Configuratie klaar",
            command=klaarKnopCommand,
            border_color="black",
            border_width=2,
        ).pack(pady=(8, 0))

        # ── preview-kolom ──────────────────────────────────────────────────
        preview_frame = customtkinter.CTkFrame(popup, fg_color="#F8F7F2",
                                               corner_radius=8)
        preview_frame.grid(row=0, column=1, sticky="nsew",
                           padx=(5, 10), pady=10)

        customtkinter.CTkLabel(
            preview_frame, text="Formatie preview",
            font=("Arial", 12, "bold"), text_color="#333333",
        ).pack(pady=(8, 2))

        import tkinter as tk
        preview_w, preview_h = 650, 280
        canvas = tk.Canvas(preview_frame,
                           width=preview_w, height=preview_h,
                           bg="#F8F7F2", highlightthickness=0)
        canvas.pack(padx=8, pady=(0, 8))

        # eerste teken — robot altijd zichtbaar vanaf het begin
        _redraw_preview()

    # ── statische hulpfunctie ──────────────────────────────────────────────
    @staticmethod
    def _robot_index_static(robot_name, robot_list):
        try:
            return robot_list.index(robot_name)
        except ValueError:
            return 0
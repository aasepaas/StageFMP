import customtkinter
import math


# ─────────────────────────────────────────────
#  Afstanden
# ─────────────────────────────────────────────
CROW_TAPER_STEPS     = 2          # schuine kegels
CROW_TAPER_ALONG_PX  = 40         # pixels per taper-stap (preview)
CROW_PARALLEL_PX     = 28         # pixels per parallelle kegel (preview)
CROW_LATERAL_PX      = 28         # maximale zijdelingse verschuiving in preview

STANDAARD_SPACING_M  = 10.0       # afstand voor "standaard 10 m" mode (meters)
CROW_TAPER_ALONG_M   = 25.0       # langs-afstand per taper-kegel (meters)
CROW_PARALLEL_DIST_M = 10.0       # langs-afstand per parallelle kegel (meters)

ROBOT_RADIUS         = 6          # visuele straal robot-cirkel in canvas px


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
        popup.geometry("980x320")
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
            """
            Hertekent de canvas preview.

            Standaard-modus: alle kegels op gelijke afstand langs de lijn.
            CROW-modus:
              - kegel 1 & 2: schuin (taper), loodrecht verschoven naar rijbaan
              - kegel 3+   : parallel aan de vluchtstrooklijn
            """
            canvas.delete("all")

            aantal_val = chosenSettings["Aantal"]
            formatie   = chosenSettings["Formatie"] or "Standaard 10m afstand"
            robot_val  = chosenSettings["RobotStart"]
            is_crow    = "CROW" in formatie

            n_extra = int(aantal_val) if aantal_val is not None else 0
            n_total = 1 + n_extra

            # ── coördinaten per kegel bepalen ─────────────────────────────
            # R = kegelrobot (slot 0), altijd op basislijn
            # vluchtstrooklijn loopt horizontaal op road_y
            road_y    = preview_h // 3 + 10   # y van vluchtstrooklijn
            rijbaan_y = road_y - 55            # rijbaankant (boven)
            margin_x  = 40
            start_x   = margin_x              # x van de robot (slot 0)

            positions = []   # lijst van (x, y) per kegel

            # Slot 0: de robot, op de vluchtstrooklijn
            positions.append((start_x, road_y))

            for i in range(1, n_total):
                if is_crow:
                    if i <= CROW_TAPER_STEPS:
                        # schuine kegel: langs + zijdelings
                        along_px   = CROW_TAPER_ALONG_PX * i
                        fraction   = (CROW_TAPER_STEPS - i + 1) / CROW_TAPER_STEPS
                        lateral_px = CROW_LATERAL_PX * fraction
                        x = start_x + along_px
                        y = road_y - lateral_px   # naar rijbaan toe = omhoog
                    else:
                        # parallel kegel
                        parallel_idx = i - CROW_TAPER_STEPS
                        along_px = (CROW_TAPER_ALONG_PX * CROW_TAPER_STEPS
                                    + CROW_PARALLEL_PX * parallel_idx)
                        x = start_x + along_px
                        y = road_y
                else:
                    # standaard: gelijke afstand langs lijn
                    spacing_px = (preview_w - 2 * margin_x) / max(n_total, 2) * 0.85
                    x = start_x + spacing_px * i
                    y = road_y

                positions.append((x, y))

            # ── rijbaanachtergrond ────────────────────────────────────────
            canvas.create_rectangle(
                0, rijbaan_y - 10, preview_w, road_y + 18,
                fill="#E8E4D9", outline="", tags="road",
            )
            # streepjes op rijbaan
            canvas.create_line(
                0, rijbaan_y, preview_w, rijbaan_y,
                fill="white", width=4
            )
            # vluchtstrookgrens (kantstreep)
            canvas.create_line(
                0, road_y - 2, preview_w, road_y - 2,
                fill="#FFD700", width=2, dash=(8, 4)
            )
            canvas.create_text(
                preview_w - 6, road_y - 10,
                text="vluchtstrook", anchor="e",
                fill="#888", font=("Arial", 8)
            )

            # ── verbindingslijn tussen schuine kegels (CROW-modus) ────────
            if is_crow and n_total > 1:
                line_pts = []
                for i, (x, y) in enumerate(positions):
                    if i == 0 or i <= CROW_TAPER_STEPS:
                        line_pts += [x, y]
                    else:
                        break
                if len(line_pts) >= 4:
                    canvas.create_line(*line_pts, fill="#999", width=1,
                                       dash=(4, 3))

            # ── afstandslabel ─────────────────────────────────────────────
            if n_total > 1:
                x0, _ = positions[0]
                x1, _ = positions[1]
                arr_y  = road_y + 28
                if is_crow:
                    label_txt = f"{CROW_TAPER_ALONG_M:.0f} m (langs)"
                else:
                    label_txt = f"{STANDAARD_SPACING_M:.1f} m"
                canvas.create_line(x0, arr_y, x1, arr_y, fill="#666", width=1,
                                   arrow="both", arrowshape=(5, 6, 3))
                canvas.create_text((x0 + x1) / 2, arr_y + 10,
                                   text=label_txt,
                                   fill="#555", font=("Arial", 9))

            # ── kegels tekenen ────────────────────────────────────────────
            for i, (x, y) in enumerate(positions):
                is_robot   = (i == 0)
                cone_color = "#FF6B35" if not is_robot else "#2563EB"
                cone_stroke= "#CC4400" if not is_robot else "#1D4ED8"

                base_half = 9
                tip_y     = y - 23
                base_y    = y

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

                # label
                label_y = tip_y - 12
                if is_robot:
                    canvas.create_text(x, label_y, text="R",
                                       fill=cone_color, font=("Arial", 9, "bold"))
                elif is_crow and i <= CROW_TAPER_STEPS:
                    canvas.create_text(x, label_y, text=f"{i}↗",
                                       fill=cone_color, font=("Arial", 8, "bold"))
                else:
                    canvas.create_text(x, label_y, text=str(i),
                                       fill=cone_color, font=("Arial", 9, "bold"))

                # robot-indicator onder de weg
                if is_robot:
                    ry = road_y + 60
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
            leg_y = preview_h - 100
            # robot
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
            # CROW-legenda
            if is_crow:
                canvas.create_text(8, leg_y + 16,
                                   text=f"↗ = schuine kegel (taper, {CROW_TAPER_STEPS}x)   "
                                        f"| = parallelle kegel",
                                   anchor="w", fill="#666", font=("Arial", 8))

            # totaal
            canvas.create_text(8, leg_y + 30,
                               text=f"Totaal aantal kegels: {n_total}",
                               anchor="w", fill="#111", font=("Arial", 11, "bold"))

            # foutmeldingen
            self.errorMsgAmountRobot = canvas.create_text(
                8, leg_y + 52,
                text=f"Waarschuwing: {n_total} totale posities, "
                     f"maar alleen {self.amountOfRobots} kegelrobots online.",
                anchor="w", fill="red", font=("Arial", 10, "bold"),
                state="hidden"
            )
            self.errorMsgFormationAmountRobots = canvas.create_text(
                8, leg_y + 74,
                text=f"Waarschuwing: CROW-formatie vereist minimaal "
                     f"{CROW_TAPER_STEPS + 1 + 1} kegels totaal "
                     f"(minstens {CROW_TAPER_STEPS + 1} extra).",
                anchor="w", fill="red", font=("Arial", 10, "bold"),
                state="hidden"
            )

        # ── callback helpers ───────────────────────────────────────────────
        def change_val(value):
            try:
                chosenSettings["Aantal"] = int(value)
                _redraw_preview()
                if (int(value) + 1) > self.amountOfRobots:
                    canvas.itemconfig(self.errorMsgAmountRobot, state="normal")
                else:
                    canvas.itemconfig(self.errorMsgAmountRobot, state="hidden")
            except Exception:
                pass

        def changeFormation(formation):
            min_crow = CROW_TAPER_STEPS + 1   # minstens 3 extra kegels nodig
            try:
                if "CROW" in formation and (
                    chosenSettings["Aantal"] is None
                    or (chosenSettings["Aantal"] + 1) < min_crow + 1
                ):
                    canvas.itemconfig(
                        self.errorMsgFormationAmountRobots, state="normal")
                    self.optionformation.set("Standaard 10m afstand")
                    chosenSettings["Formatie"] = "Standaard 10m afstand"
                    return
                else:
                    canvas.itemconfig(
                        self.errorMsgFormationAmountRobots, state="hidden")
            except Exception:
                pass
            chosenSettings["Formatie"] = formation
            _redraw_preview()

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
        preview_w, preview_h = 700, 310
        canvas = tk.Canvas(preview_frame,
                           width=preview_w, height=preview_h,
                           bg="#F8F7F2", highlightthickness=0)
        canvas.pack(padx=8, pady=(0, 8))

        _redraw_preview()

    # ── statische hulpfunctie ──────────────────────────────────────────────
    @staticmethod
    def _robot_index_static(robot_name, robot_list):
        try:
            return robot_list.index(robot_name)
        except ValueError:
            return 0
import customtkinter

class AppFrame(customtkinter.CTkFrame):
    def __init__(self, master, values, masterCallbackFunction):
        super().__init__(master)
        self.amountBoxes = values
        self.checkboxes = []

        for i,value in enumerate(self.amountBoxes):
            checkbox = customtkinter.CTkCheckBox(self, text=value,command = masterCallbackFunction)
            checkbox.grid(row=i, column = 0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checkedCheckboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get():
                checkedCheckboxes.append(checkbox.cget("text"))

        return checkedCheckboxes

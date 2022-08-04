import tkinter as tk

class EnhancedListbox(tk.Listbox):

    def __init__(self, parent, *args, **kwargs):

        super(EnhancedListbox, self).__init__()

        self.selected_file = ""
        self.parent = parent

        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Write", command=self.write_file)
        self.bind("<Button-3>", self.popup)
        self.bind("<<ListboxSelect>>", self.on_select)

    def on_select(self, event):
        """
        Handle when an item is selected in the list box
        """
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            data = event.widget.get(index)
            self.selected_file = data

    def popup(self, event):
        """
        Handles right click context popup
        """
        self.selection_clear(0, tk.END)
        self.selection_set(self.nearest(event.y))
        self.activate(self.nearest(event.y))
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def write_file(self):
        """
        Handles writing single file
        """
        for i in self.curselection()[::-1]:
            data = self.get(i)
            self.parent.writer.write_single_drive(data)
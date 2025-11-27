from src.interface.gui import ChromaApp

if __name__ == "__main__":
    app = ChromaApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
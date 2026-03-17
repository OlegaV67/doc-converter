import sys
from pathlib import Path

# В режиме PyInstaller все модули лежат в sys._MEIPASS
if getattr(sys, "frozen", False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

sys.path.insert(0, str(base_path))

from ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

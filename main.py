import sys
from pathlib import Path

# В режиме PyInstaller все модули лежат в sys._MEIPASS
if getattr(sys, "frozen", False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

sys.path.insert(0, str(base_path))

from ui.app import App
from utils.license_client import check_license
from ui.activation_dialog import ActivationDialog


def main():
    app = App()

    if not check_license():
        dialog = ActivationDialog(app)
        app.wait_window(dialog)
        if not dialog.activated:
            app.destroy()
            sys.exit(0)

    app.mainloop()


if __name__ == "__main__":
    main()

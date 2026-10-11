"""System tray icon integration using pystray for desktop controls and state feedback."""

import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray
from utils.logger import get_logger

class SystemTrayApp:
    """Manages system tray menu, icon generation, and user control callbacks."""

    def __init__(
        self,
        on_pause_monitoring: Callable[[], None],
        on_resume_monitoring: Callable[[], None],
        is_monitoring: Callable[[], bool],
        on_pause_audio: Callable[[], None],
        on_resume_audio: Callable[[], None],
        on_skip_document: Callable[[], None],
        on_stop_audio: Callable[[], None],
        on_replay_document: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        """Initializes tray application callbacks and menu structures."""
        self.on_pause_monitoring = on_pause_monitoring
        self.on_resume_monitoring = on_resume_monitoring
        self.is_monitoring = is_monitoring
        self.on_pause_audio = on_pause_audio
        self.on_resume_audio = on_resume_audio
        self.on_skip_document = on_skip_document
        self.on_stop_audio = on_stop_audio
        self.on_replay_document = on_replay_document
        self.on_exit = on_exit

        self.logger = get_logger()
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _create_icon_image(self, color="navy") -> Image.Image:
        """Generates a dynamic 64x64 icon image for the system tray."""
        image = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Outer circle
        draw.ellipse((4, 4, 60, 60), fill=color)
        # Soundwave / audio icon lines
        draw.line((20, 32, 20, 32), fill="white", width=4)
        draw.line((28, 20, 28, 44), fill="white", width=4)
        draw.line((36, 14, 36, 50), fill="white", width=4)
        draw.line((44, 24, 44, 40), fill="white", width=4)
        return image

    def _toggle_monitoring(self, item=None) -> None:
        """Toggles clipboard monitoring state."""
        if self.is_monitoring():
            self.on_pause_monitoring()
        else:
            self.on_resume_monitoring()
        if self.icon:
            self.icon.update_menu()

    def _build_menu(self) -> pystray.Menu:
        """Constructs system tray context menu items."""
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: "⏸️ Pause Monitoring" if self.is_monitoring() else "▶️ Resume Monitoring",
                self._toggle_monitoring
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏯️ Pause Audio", lambda: self.on_pause_audio()),
            pystray.MenuItem("▶️ Resume Audio", lambda: self.on_resume_audio()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏭️ Skip Current Document", lambda: self.on_skip_document()),
            pystray.MenuItem("🔁 Replay Current Document", lambda: self.on_replay_document()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏹️ Stop Audio", lambda: self.on_stop_audio()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit AI Listener", lambda: self.stop())
        )

    def _setup_left_click(self) -> None:
        """Hooks left-click on Windows pystray icon to open the popup menu."""
        if self.icon and hasattr(self.icon, '_message_handlers'):
            try:
                import pystray._win32 as pystray_win32
                orig_notify = self.icon._on_notify
                def custom_notify(wparam, lparam):
                    if lparam == pystray_win32.win32.WM_LBUTTONUP:
                        lparam = pystray_win32.win32.WM_RBUTTONUP
                    return orig_notify(wparam, lparam)
                self.icon._message_handlers[pystray_win32.win32.WM_NOTIFY] = custom_notify
            except Exception as e:
                self.logger.debug(f"Left-click hook skipped or unsupported: {e}")

    def start_non_blocking(self) -> None:
        """Starts system tray icon in a dedicated background thread."""
        self.icon = pystray.Icon(
            "AIListener",
            icon=self._create_icon_image("navy"),
            title="AI Listener - Active",
            menu=self._build_menu()
        )
        self._setup_left_click()
        self._thread = threading.Thread(target=self.icon.run, daemon=True, name="TrayIconThread")
        self._thread.start()
        self.logger.info("System tray icon started.")

    def notify(self, message: str, title: Optional[str] = None) -> None:
        """Shows a balloon/toast notification from the tray icon, if supported."""
        if not self.icon:
            return
        try:
            self.icon.notify(message, title or "AI Listener")
        except Exception as e:
            self.logger.debug(f"Tray notification skipped or unsupported: {e}")

    def set_title(self, title: str) -> None:
        """Updates the tray icon tooltip text."""
        if self.icon:
            self.icon.title = title

    def run(self, on_ready: Optional[Callable[["SystemTrayApp"], None]] = None) -> None:
        """Runs system tray icon loop on the main thread (blocking).

        The icon is made visible immediately; if on_ready is provided it runs in a
        background thread afterwards, so slow startup work never delays the icon.
        """
        self.icon = pystray.Icon(
            "AIListener",
            icon=self._create_icon_image("navy"),
            title="AI Listener - Starting...",
            menu=self._build_menu()
        )
        self._setup_left_click()

        def setup(icon) -> None:
            icon.visible = True
            self.logger.info("System tray icon is now visible.")
            if on_ready:
                on_ready(self)

        self.logger.info("System tray icon running on main thread.")
        self.icon.run(setup=setup)

    def stop(self) -> None:
        """Stops system tray icon."""
        self.logger.info("Stopping system tray application...")
        if self.icon:
            self.icon.stop()

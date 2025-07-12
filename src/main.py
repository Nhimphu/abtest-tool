"""Entry point for launching the GUI application."""

# Ensure optional plugins are loaded on startup
import plugin_loader

from ui.main import main

if __name__ == "__main__":
    main()

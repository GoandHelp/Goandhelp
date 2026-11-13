import os

import reflex as rx

# The managed database provides the connection URL through the environment.
# Prefer REFLEX_DB_URL, fall back to DATABASE_URL. Never hardcode credentials.
DB_URL = os.environ.get("REFLEX_DB_URL") or os.environ.get("DATABASE_URL")

config = rx.Config(
    app_name="app",
    default_color_mode="light",
    db_url=DB_URL,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        # The theme is owned by the Radix plugin (the supported path in
        # Reflex 0.9+); `rx.App(theme=...)` is deprecated.
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="inherit",
                accent_color="orange",
                gray_color="gray",
            )
        ),
    ],
)

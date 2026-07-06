"""Floating overlay window for major events. Runs as a subprocess with its own NSApp."""

import argparse
import sys
import time

from AppKit import (
    NSApplication,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSMakeRect,
    NSScreen,
    NSTextField,
    NSTimer,
    NSView,
    NSWindow,
    NSWorkspace,
)
from CoreFoundation import CFRunLoopGetMain, CFRunLoopStop
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowBounds,
    kCGWindowLayer,
    kCGWindowListExcludeDesktopElements,
    kCGWindowListOptionOnScreenOnly,
    kCGWindowOwnerPID,
)

EFFECTS = {
    "success": {
        "emoji": "\u2705",
        "label": "SUCCESS",
        "bg": (0.1, 0.6, 0.2, 0.92),
        "border": (0.2, 0.9, 0.3, 1.0),
    },
    "error": {
        "emoji": "\u274c",
        "label": "ERROR",
        "bg": (0.7, 0.1, 0.1, 0.92),
        "border": (1.0, 0.2, 0.2, 1.0),
    },
    "start": {
        "emoji": "\U0001f3ae",
        "label": "ARCADE",
        "bg": (0.1, 0.2, 0.6, 0.92),
        "border": (0.3, 0.5, 1.0, 1.0),
    },
}

WIDTH, HEIGHT = 380, 72


def _make_label(text, font, color, frame):
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setStringValue_(text)
    label.setFont_(font)
    label.setTextColor_(color)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    return label


def _terminal_window_frame():
    """Find the frontmost application's main window frame."""
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if not app:
        return None
    pid = app.processIdentifier()
    options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
    window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    if not window_list:
        return None
    for info in window_list:
        if info.get(kCGWindowOwnerPID) != pid:
            continue
        if info.get(kCGWindowLayer, -1) != 0:
            continue
        b = info.get(kCGWindowBounds)
        if not b:
            continue
        screen = NSScreen.mainScreen()
        if not screen:
            continue
        sh = screen.frame().size.height
        return NSMakeRect(b["X"], sh - b["Y"] - b["Height"], b["Width"], b["Height"])
    return None


def show_overlay(effect_name, message, duration):
    config = EFFECTS.get(effect_name)
    if not config:
        print(f"Unknown effect: {effect_name}", file=sys.stderr)
        sys.exit(1)

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)  # Accessory — no dock icon

    term = _terminal_window_frame()
    if term:
        tx, ty, tw, th = term.origin.x, term.origin.y, term.size.width, term.size.height
    else:
        tx, ty, tw, th = 200, 200, 800, 600

    margin = 24
    ox = tx + tw - WIDTH - margin
    oy = ty + th - HEIGHT - margin - 40

    frame = NSMakeRect(ox, oy, WIDTH, HEIGHT)
    start_frame = NSMakeRect(ox + WIDTH + margin, oy, WIDTH, HEIGHT)

    # Window
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        start_frame, 0, NSBackingStoreBuffered, False
    )
    window.setLevel_(3)  # Floating
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setHasShadow_(True)
    window.setIgnoresMouseEvents_(True)

    # Content view with rounded background
    content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, WIDTH, HEIGHT))
    content.setWantsLayer_(True)
    layer = content.layer()
    layer.setCornerRadius_(16)
    layer.setBackgroundColor_(
        NSColor.colorWithRed_green_blue_alpha_(*config["bg"]).CGColor()
    )
    layer.setBorderColor_(
        NSColor.colorWithRed_green_blue_alpha_(*config["border"]).CGColor()
    )
    layer.setBorderWidth_(3)

    # Emoji
    emoji_label = _make_label(
        config["emoji"],
        NSFont.systemFontOfSize_(36),
        NSColor.whiteColor(),
        NSMakeRect(16, 10, 48, 50),
    )
    content.addSubview_(emoji_label)

    # Title
    title_label = _make_label(
        config["label"],
        NSFont.boldSystemFontOfSize_(18),
        NSColor.whiteColor(),
        NSMakeRect(68, 34, 290, 28),
    )
    content.addSubview_(title_label)

    # Message
    msg_label = _make_label(
        message,
        NSFont.systemFontOfSize_(13),
        NSColor.whiteColor().colorWithAlphaComponent_(0.85),
        NSMakeRect(68, 10, 290, 24),
    )
    content.addSubview_(msg_label)

    window.setContentView_(content)
    window.setAlphaValue_(0.0)
    window.makeKeyAndOrderFront_(None)

    # Slide in
    window.setFrame_display_animate_(frame, True, True)
    window.setAlphaValue_(1.0)

    # Shake for error
    if effect_name == "error":
        def shake_step(offsets, idx=0):
            if idx >= len(offsets):
                return
            f = window.frame()
            f.origin.x = frame.origin.x + offsets[idx]
            window.setFrame_display_(f, True)
            NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                0.04, False, lambda _t: shake_step(offsets, idx + 1)
            )

        NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            0.4, False, lambda _t: shake_step([8, -8, 6, -6, 3, -3, 0])
        )

    # Fade out and exit
    def fade_and_exit(_timer):
        steps = 10
        for i in range(steps):
            window.setAlphaValue_(1.0 - (i + 1) / steps)
            time.sleep(0.05)
        CFRunLoopStop(CFRunLoopGetMain())

    NSTimer.scheduledTimerWithTimeInterval_repeats_block_(duration, False, fade_and_exit)
    app.run()


def main():
    parser = argparse.ArgumentParser(description="Arcade visual overlay")
    parser.add_argument("--effect", required=True, choices=EFFECTS.keys())
    parser.add_argument("--message", default="")
    parser.add_argument("--duration", type=float, default=3.0)
    args = parser.parse_args()
    show_overlay(args.effect, args.message, args.duration)


if __name__ == "__main__":
    main()

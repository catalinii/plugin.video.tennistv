# -*- coding: utf-8 -*-
"""Tennis TV addon for Kodi."""

import sys
from urllib.parse import parse_qs, urlencode, urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib import api

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")

BASE_URL = sys.argv[0]
HANDLE = int(sys.argv[1])
ARGS = parse_qs(sys.argv[2][1:])


def log(message):
    xbmc.log("[%s] %s" % (ADDON_ID, message), xbmc.LOGINFO)


def token_file():
    profile = ADDON.getAddonInfo("profile")
    directory = xbmcvfs.translatePath(profile)
    return xbmcvfs.translatePath("%s/tokens.json" % profile)


def get_client():
    return api.TennisTV(
        username=ADDON.getSetting("username"),
        password=ADDON.getSetting("password"),
        token_file=token_file(),
    )


def build_url(**kwargs):
    return "%s?%s" % (BASE_URL, urlencode(kwargs))


def notify(message, heading=None):
    xbmcgui.Dialog().notification(
        heading or ADDON_NAME, message, xbmcgui.NOTIFICATION_ERROR
    )


def add_menu_item(label, url, icon=""):
    item = xbmcgui.ListItem(label)
    xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)


def add_video_item(label, url, plot="", duration=0):
    item = xbmcgui.ListItem(label)
    info = {"title": label, "mediatype": "video"}
    if plot:
        info["plot"] = plot
    if duration:
        info["duration"] = duration
    item.setInfo("video", info)
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=False)


def add_info_item(label, plot=""):
    item = xbmcgui.ListItem(label)
    item.setInfo("video", {"title": label, "plot": plot, "mediatype": "video"})
    xbmcplugin.addDirectoryItem(HANDLE, "", item, isFolder=False)


# ---------------------------------------------------------------------- #
# Menus
# ---------------------------------------------------------------------- #
def show_main_menu():
    add_menu_item("Live Now", build_url(mode="live"))
    add_menu_item("Upcoming", build_url(mode="upcoming"))
    xbmcplugin.endOfDirectory(HANDLE)


def show_live():
    client = get_client()
    try:
        matches = client.live_matches()
        videos = client.live_videos()
    except Exception as exc:
        log("Failed to load live matches: %s" % exc)
        notify("Failed to load live matches.")
        xbmcplugin.endOfDirectory(HANDLE)
        return

    world_feed = next(
        (
            v
            for v in videos
            if (v.get("additionalInfo") or {}).get("court_id", "").strip('"')
            == "WORLD_FEED"
        ),
        None,
    )

    if world_feed:
        media_id = world_feed.get("mediaId")
        add_video_item(
            "World Feed",
            build_url(mode="play", media_id=media_id, title="World Feed"),
            plot=world_feed.get("description") or "",
        )

    for match in matches:
        video = api.find_video_for_match(match, videos)
        title = api.match_title(match)
        plot = (match.get("metadata") or {}).get("description") or ""
        score = api.match_scores(match)
        label = title
        if score:
            label = "%s  [B][LIVE %s][/B]" % (title, score)

        if video:
            media_id = video.get("mediaId")
            add_video_item(
                label,
                build_url(mode="play", media_id=media_id, title=title),
                plot=plot,
            )
        else:
            add_info_item(label, plot)

    if not matches and not world_feed:
        add_info_item("No live matches right now.")

    xbmcplugin.endOfDirectory(HANDLE)


def show_upcoming():
    client = get_client()
    try:
        matches = client.upcoming_matches()
    except Exception as exc:
        log("Failed to load upcoming matches: %s" % exc)
        notify("Failed to load upcoming matches.")
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for match in matches:
        p1, p2 = api.match_players(match)
        label = "%s vs %s" % (p1 or "TBD", p2 or "TBD")

        when = match.get("NotBeforeText") or ""
        if match.get("NotBefore") and match.get("NotBefore") not in (
            "Followed By",
            "",
        ):
            when = "%s %s" % (when, match["NotBefore"]).strip()
        elif when:
            pass

        details = []
        if match.get("CourtName"):
            details.append(match["CourtName"])
        if match.get("Round") and isinstance(match["Round"], dict):
            details.append(match["Round"].get("RoundName", ""))
        if when:
            details.append(when)
        if details:
            label = "%s  [COLOR grey][%s][/COLOR]" % (label, " | ".join(details))

        plot = (match.get("metadata") or {}).get("description") or ""
        add_info_item(label, plot)

    if not matches:
        add_info_item("No upcoming matches scheduled.")

    xbmcplugin.endOfDirectory(HANDLE)


def play():
    media_id = ARGS.get("media_id", [None])[0]
    title = ARGS.get("title", ["Tennis TV"])[0]
    if not media_id:
        notify("No stream specified.")
        return

    client = get_client()
    try:
        stream_url = client.stream_url(media_id)
    except api.TennisTVAuthError as exc:
        log("Auth error: %s" % exc)
        notify(str(exc))
        return
    except Exception as exc:
        log("Failed to resolve stream: %s" % exc)
        notify("Failed to resolve stream.")
        return

    item = xbmcgui.ListItem(title)
    item.setPath(stream_url)
    item.setInfo("video", {"title": title, "mediatype": "video"})
    item.setProperty("IsPlayable", "true")

    if _has_inputstream_adaptive():
        item.setMimeType("application/vnd.apple.mpegurl")
        item.setContentLookup(False)
        item.setProperty("inputstream", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", "hls")
    else:
        item.setMimeType("application/vnd.apple.mpegurl")

    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def _has_inputstream_adaptive():
    try:
        return xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)")
    except Exception:
        return False


def router():
    mode = ARGS.get("mode", [None])[0]
    if mode == "live":
        show_live()
    elif mode == "upcoming":
        show_upcoming()
    elif mode == "play":
        play()
    else:
        show_main_menu()


if __name__ == "__main__":
    router()

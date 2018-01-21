import html
import os
import re
import urllib.request, urllib.error, urllib.parse
from aqt.utils import showInfo, showWarning, askUser
from aqt import mw
from anki.utils import intTime, checksum
from anki.hooks import addHook

internailze_ask_backup = True

def onShowDeckOptions(m, did):
    a = m.addAction("Internalize Media")
    a.triggered.connect(lambda b, did=did: internailzeMedia(did))


def retrieveURL(mw, url):
    """Download file into media folder and return local filename or None."""
    req = urllib.request.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
    resp = urllib.request.urlopen(req)
    ct = resp.info().get("content-type")
    filecontents = resp.read()
    # strip off any query string
    url = re.sub(r"\?.*?$", "", url)
    path = urllib.parse.unquote(url)
    fname = os.path.basename(path)
    if not fname:
        fname = checksum(filecontents)
    return mw.col.media.writeData(fname, filecontents, typeHint=ct)


def internailzeMedia(did):
    """Search http-referenced resources in notes, download them into local storage and change the references."""
    global internailze_ask_backup
    if internailze_ask_backup and not askUser("Have you backed up your collection and media folder?"):
        return
    internailze_ask_backup = False  # don't ask again
    affected_count = 0
    # regex for <img>
    patternImg = re.compile('<img[^>]+?(https?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+)[^>]*>', re.IGNORECASE)
    # regex for [sound]
    patternSound = re.compile('\[sound:[^\]]*(https?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+)[^\]]*\]', re.IGNORECASE)
    deck = mw.col.decks.get(did)
    nids = mw.col.db.list(
        "select distinct notes.id from notes inner join cards on notes.id = cards.nid where cards.did = %d and (lower(notes.flds) like '%%http://%%' or lower(notes.flds) like '%%https://%%')" %
        deck["id"])
    mw.progress.start(max=len(nids), min=0, immediate=True)
    try:
        for nid in nids:
            note = mw.col.getNote(nid)
            changed = False
            for fld, val in note.items():
                mapUnescape = lambda x: (x, html.unescape(x))
                mapDoNothing = lambda x: (x, x)
                # fieldUrl - url representation in a field
                # url - clean url
                for fieldUrl, url in list(map(mapDoNothing, re.findall(patternImg, val))) \
                        + list(map(mapUnescape, re.findall(patternSound, val))):
                    try:
                        filename = retrieveURL(mw, url)
                        if filename:
                            val = val.replace(fieldUrl, filename)
                            note[fld] = val
                            changed = True
                    except urllib.error.URLError as e:
                        if not askUser("An error occurred while opening %s\n%s\n\nDo you want to proceed?" % (url.encode("utf8"), e)):
                            return
            if changed:
                note.flush(intTime())
                affected_count += 1
            mw.progress.update()
    finally:
        if affected_count > 0:
            mw.col.media.findChanges()
        mw.progress.finish()
        showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affected_count))


addHook("showDeckOptions", onShowDeckOptions)
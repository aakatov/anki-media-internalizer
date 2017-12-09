import re
import urllib.request, urllib.error, urllib.parse
from aqt.utils import showInfo, showWarning, askUser
from aqt import mw
from aqt.qt import *
from anki.utils import intTime
from anki import version
from anki.hooks import addHook
from aqt.deckbrowser import DeckBrowser


def onShowDeckOptions(m, did):
    a = m.addAction("Internalize Media")
    a.triggered.connect(lambda b, did=did: internailzeMedia(did))


def retrieveURL(mw, url):
    """Download file into media folder and return local filename or None."""
    req = urllib.request.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
    filecontents = urllib.request.urlopen(req).read()
    path = urllib.parse.unquote(url)
    return mw.col.media.writeData(path, filecontents)

internailze_ask_backup = True

def internailzeMedia(did):
    """Search http-referenced resources in notes, download them into local storage and change the references."""
    global internailze_ask_backup
    if internailze_ask_backup and not askUser("Have you backed up your collection and media folder?"):
        return
    internailze_ask_backup = False  # don't ask again
    affected_count = 0
    pattern = re.compile('<[^>]+(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)[^>]*>')
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
                for url in re.findall(pattern, val):
                    try:
                        filename = retrieveURL(mw, url)
                        if filename:
                            val = val.replace(url, filename)
                            changed = True
                    except urllib.error.URLError as e:
                        if not askUser("An error occurred while opening %s\n%s\n\nDo you want to proceed?" % (url, e)):
                            return
            if changed:
                note[fld] = val
                note.flush(intTime())
                affected_count += 1
            mw.progress.update()
    finally:
        if affected_count > 0:
            mw.col.media.findChanges()
        mw.progress.finish()
        showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affected_count))


addHook("showDeckOptions", onShowDeckOptions)
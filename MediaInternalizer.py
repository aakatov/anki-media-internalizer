from aqt import mw
from aqt.utils import showInfo, showWarning
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from anki.notes import Note
import re
import urllib2


def myShowOptions(self, did):
    "Monkey patching of DeckBrowser._showOptions."
    m = QMenu(self.mw)
    a = m.addAction(_("Rename"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._rename(did))
    a = m.addAction(_("Options"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._options(did))
    a = m.addAction(_("Export"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._export(did))
    a = m.addAction(_("Delete"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._delete(did))
    # add the menu item if the deck is not dynamic
    deck = self.mw.col.decks.get(did)
    if not deck['dyn']:
        a = m.addAction("Internalize media")
        a.connect(a, SIGNAL("triggered()"), lambda did=did: self._internalize(did))
    m.exec_(QCursor.pos())


def retrieveURL(mw, url):
    "Download file into media folder and return local filename or None."
    try:
        req = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
        filecontents = urllib2.urlopen(req).read()
    except urllib2.URLError, e:
        showWarning("An error occurred while opening %s\n %s" % (url, e))
        return
    path = unicode(urllib2.unquote(url.encode("utf8")), "utf8")
    return mw.col.media.writeData(path, filecontents)


def internailzeMedia(self, did):
    "Search http-referenced resources in notes, download them into local storage and change the references."
    affectedCount = 0
    urlPattern = re.compile('(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')
    deck = self.mw.col.decks.get(did)
    noteIds = mw.col.db.list(
        "select distinct notes.id from notes inner join cards on notes.id = cards.nid where cards.did = %d and (notes.flds like '%%http://%%' or notes.flds like '%%https://%%')" %
        deck["id"])
    mw.progress.start(max=len(noteIds), min=0, immediate=True)
    try:
        for nid in noteIds:
            note = Note(mw.col, id=nid)
            changed = False
            for fld, val in note.items():
                for url in re.findall(urlPattern, val):
                    filename = retrieveURL(mw, url)
                    if filename:
                        val = val.replace(url, filename)
                        changed = True
                note[fld] = val
            if changed:
                note.flush()
                affectedCount += 1
            mw.progress.update()
    finally:
        mw.progress.finish()
    showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affectedCount))


DeckBrowser._showOptions = myShowOptions
DeckBrowser._internalize = internailzeMedia
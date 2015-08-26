import re
import urllib2
from aqt import mw
from aqt.utils import showInfo, showWarning, askUser
from aqt.qt import *
from anki.utils import intTime
from aqt.deckbrowser import DeckBrowser
from anki.notes import Note


def myShowOptions(self, did):
    """Monkey patching of DeckBrowser._showOptions."""
    m = QMenu(self.mw)
    a = m.addAction(_("Rename"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._rename(did))
    a = m.addAction(_("Options"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._options(did))
    a = m.addAction(_("Export"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._export(did))
    a = m.addAction(_("Delete"))
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._delete(did))
    # add the menu item
    a = m.addAction("Internalize Media")
    a.connect(a, SIGNAL("triggered()"), lambda did=did: self._internalize(did))
    m.exec_(QCursor.pos())


def retrieveURL(mw, url):
    """Download file into media folder and return local filename or None."""
    req = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
    filecontents = urllib2.urlopen(req).read()
    path = unicode(urllib2.unquote(url.encode("utf8")), "utf8")
    return mw.col.media.writeData(path, filecontents)


def internailzeMedia(self, did):
    """Search http-referenced resources in notes, download them into local storage and change the references."""
    if not askUser("Have you backed up your collection and media folder?"):
        return
    affected_count = 0
    pattern = re.compile('<[^>]+(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)[^>]*>',
                         re.IGNORECASE)
    deck = self.mw.col.decks.get(did)
    nids = mw.col.db.list(
        "select distinct notes.id from notes inner join cards on notes.id = cards.nid where cards.did = %d and (lower(notes.flds) like '%%http://%%' or lower(notes.flds) like '%%https://%%')" %
        deck["id"])
    mw.progress.start(max=len(nids), min=0, immediate=True)
    try:
        for nid in nids:
            note = Note(mw.col, id=nid)
            changed = False
            for fld, val in note.items():
                for url in re.findall(pattern, val):
                    try:
                        filename = retrieveURL(mw, url)
                        if filename:
                            val = val.replace(url, filename)
                            changed = True
                    except urllib2.URLError as e:
                        if not askUser("An error occurred while opening %s\n%s\n\nDo you want to proceed?" % (url, e)):
                            return
                note[fld] = val
            if changed:
                note.flush(intTime())
                affected_count += 1
            mw.progress.update()
    finally:
        if affected_count > 0:
            mw.col.media.findChanges()
        mw.progress.finish()
        showInfo("Deck: %s\nNotes affected: %d" % (deck["name"], affected_count))


DeckBrowser._showOptions = myShowOptions
DeckBrowser._internalize = internailzeMedia
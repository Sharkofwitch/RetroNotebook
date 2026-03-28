# retro-notebook

Ein modernes, retro-inspiriertes Desktop-Notebook für Code, Mathematik, Logik und Minigames.

> **Aktuelle Version: v1.4.0**

## Features
- Hochwertige Retro-Optik (CRT-Look, Scanlines, Glow, animierte Pixel, Retro-Icons)
- Zellen für Code (eigener Interpreter), Markdown **und Tests**
- Eigener Interpreter für mathematische Ausdrücke, Variablen, Listen, Strings, Funktionen, Bedingungen, Schleifen
- **Test-Zellen** mit Assertion-Befehlen (`ASSERT`, `ASSERT_EQ`, `ASSERT_APPROX`) und farbcodiertem Ergebnis
- **Test-Runner-Panel** – alle Test-Zellen auf einmal ausführen, mit Gesamt-/Bestanden-/Fehlgeschlagen-Übersicht
- **Interaktiver Debugger** – Schritt-für-Schritt-Ausführung, Breakpoints, Variable Inspector
- **Versionsverlauf & Wiederherstellung** – automatische Snapshots bei jedem Speichern; 🕑 History-Dialog zeigt alle Snapshots mit Diff-Vorschau und ermöglicht Ein-Klick-Wiederherstellung (reversibel)
- Grafikbefehle: Punkte, Linien, Kreise (z.B. zum Plotten von Daten)
- Soundeffekte beim Ausführen und Starten
- Notebook speichern und laden (JSON, gespeichert in `~/retro-notebook-notebooks/`)
- Fehlerabfang und Endlosschleifen-Schutz
- Minigames: **CodeGrid** (Logikpuzzle, mehrere Spielmodi, Daily Challenge, XP, Highscore, Achievements, Seed-System), **Bit Factory** (Survival Builder)
- Fortschrittssystem: XP, Highscore, Achievements, Daily Challenge
- Animierte, atmosphärische Startseite und Menüs im Retro-Stil
- About-Fenster im Retro-Stil
- Drag & Drop für Zellen
- Mac-kompatibel: Ressourcen-Handling für App-Bundle vorbereitet
- Beispiel-Workflow im Ordner `docs/notebooks/`

## Installation & Start
1. Python 3.10+ installieren
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Starten:
   ```bash
   python run.py
   ```

### Als macOS-App (Bundle)
- Die App ist vorbereitet für PyInstaller, py2app oder Briefcase.
- Alle Ressourcen werden über `resource_path` geladen (funktioniert im Bundle und im Dev-Modus).
- Für ein App-Bundle: Siehe Beispiel-Specfile oder py2app-Setup (nicht im Repo enthalten).

## Sprache & Beispiele
- Variablen und Listen:
  ```
  LET x = 5
  LET arr = [10, 20, 30]
  LET arr[1] = 42
  PRINT arr[1]
  ```
- Schleifen und Bedingungen:
  ```
  LET i = 0
  WHILE i < 5 DO
      PRINT i
      LET i = i + 1
  ENDWHILE
  IF x > 3 THEN
      PRINT "x ist groß"
  ELSE
      PRINT "x ist klein"
  ENDIF
  ```
- Grafikbefehle (alle in einem Block werden gemeinsam angezeigt):
  ```
  LET arr = [20, 34, 29, 40, 32]
  LET i = 0
  WHILE i < len(arr) - 1 DO
      LET x1 = i * 20
      LET y1 = arr[i]
      LET x2 = (i + 1) * 20
      LET y2 = arr[i + 1]
      LINE x1, y1, x2, y2
      LET i = i + 1
  ENDWHILE
  ```
- Eingebaute Funktionen: `len`, `str`, `int`, `float`, `list`, `ord`, `chr`, `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`
- Minigames: Im Hauptmenü auswählbar, Fortschritt wird gespeichert.

## Test-Zellen & Assertions

Wähle den Zellentyp **Test** aus, um Assertions in eine Zelle zu schreiben:

```
# Variablen setzen, dann testen
LET x = 2 + 2
ASSERT x > 0
ASSERT_EQ x, 4
ASSERT_APPROX 3.14159, pi, 0.001
```

Unterstützte Assertion-Befehle:

| Befehl | Beschreibung |
|--------|-------------|
| `ASSERT expr` | Besteht, wenn `expr` truthy ist |
| `ASSERT_EQ a, b` | Besteht, wenn `a == b` |
| `ASSERT_APPROX a, b [, tol]` | Besteht, wenn `|a - b| ≤ tol` (Standard: `1e-6`) |

- Drücke **Run Tests** in einer Test-Zelle, um nur diese Zelle zu testen.
- Drücke **▶  Run Tests** in der Hauptleiste, um alle Test-Zellen auf einmal auszuführen.
- Das Test-Runner-Panel zeigt Gesamt-/Bestanden-/Fehlgeschlagen-Übersicht sowie Details pro Zelle.
- Durch Doppelklick auf ein Ergebnis springt der Fokus zur zugehörigen Zelle.
- Optional: Testergebnisse als JSON-Bericht speichern.
- Testergebnisse werden **nicht** automatisch im Notebook gespeichert.

## Interaktiver Debugger

Klicke **Debug** in einer Code-Zelle, um den Schritt-für-Schritt-Debugger zu öffnen:
- Zeilenweise Ausführung
- Variable Inspector nach jedem Schritt
- Breakpoints per Klick auf eine Zeile setzen/entfernen
- "Continue" führt bis zum nächsten Breakpoint aus
- Session jederzeit neu starten

## Versionsverlauf & Wiederherstellung

Klicke **🕑 History** in der Werkzeugleiste, um den Versionsverlauf des aktuellen Notebooks zu öffnen:

- Jeder manuelle Speichervorgang erstellt automatisch einen Snapshot.
- Der History-Dialog zeigt alle Snapshots (neueste zuerst) mit Zeitstempel, Grund und Zellanzahl.
- Die Vorschau zeigt den Inhalt jeder Zelle im ausgewählten Snapshot (farbkodiert nach Typ).
- Die Diff-Leiste zeigt, was sich vom Snapshot zum aktuellen Stand geändert hat.
- **Wiederherstellen** erstellt zunächst einen „Pre-restore"-Snapshot, sodass jede Wiederherstellung umkehrbar ist.
- Snapshots werden lokal in `~/retro-notebook-notebooks/.history/` gespeichert und überleben Neustarts.
- Maximal 20 Snapshots pro Notebook werden aufbewahrt (älteste werden automatisch gelöscht).

## Hinweise
- Alle Grafikbefehle in einer Codezelle werden als ein Bild angezeigt.
- WHILE/ENDWHILE, FOR/NEXT und IF/ELSE/ENDIF unterstützen Blöcke.
- Fehler in Schleifen oder Grafikbefehlen brechen die Ausführung ab.
- Maximal 1000 WHILE-Durchläufe (Schutz vor Endlosschleifen).
- Ressourcen werden immer über `resource_path` geladen (auch im App-Bundle).
- Test-Zellen werden in einer eigenen, isolierten Interpreter-Instanz ausgeführt.
- Notebooks werden in `~/retro-notebook-notebooks/` gespeichert.

## To-Do / Ideen
- Export als HTML/PDF
- Undo/Redo für einzelne Zell-Edits
- Farbschema-Auswahl (verschiedene Retro-Themes)
- Weitere Minigames und Easter Eggs
- Bessere macOS-Integration (Dock-Icon, Info.plist, App-Icon)

---

(c) 2025-2026 by Jakob Szarkowicz & Contributors  
MIT License, siehe LICENSE  
Siehe [CHANGELOG.md](CHANGELOG.md) für eine vollständige Änderungshistorie.


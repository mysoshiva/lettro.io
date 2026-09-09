# Test letter 01 — Stadt Heilbronn, vehicle address change notice

Type: fixed-deadline administrative notice
Language: German

## Input (redacted OCR text)

Stadt Heilbronn | Postfach 3440 | 74024 Heilbronn
HN Heilbronn

Herr
[NAME]
[ADDRESS]

Stadt Heilbronn
Bürgeramt
Kfz-Zulassungsstelle (im LRA)
Lerchenstr. 40
74072 Heilbronn

FOLGEN Sie der Beschilderung Landratsamt: Eingang vom Parkplatz

Ansprechpartner/in: Frau Albrich
Zimmer: [ZIMMER_NUMBER]
Telefon: 07131-56-2044
Telefax: 07131-56-2045
Mail: kfz-zulassung@heilbronn.de
Internet: heilbronn.de

Datum: 31.08.2026
Unser Zeichen: [CASE_NUMBER]

Erfüllung von Meldepflichten für Ihr Fahrzeug

amtl. Kennzeichen: [LICENSE_PLATE]
Fabrikat: FORD (D)
Fahrzeug-Typ: DFK
Fahrgestellnummer: [VIN]
Fahrzeug-Art: Fz.z.Pers.bef.b. 8 Spl.
Fahrzeug-Farbe: GRAU

Sehr geehrter Herr [NAME],

der Zulassungsbehörde wurde bekannt, dass sich Ihre Anschrift als Halter des o.a. Fahrzeugs bereits seit dem 01.03.2026 geändert hat.

Um sicherzustellen, dass die Angaben in der Zulassungsbescheinigung Teil I (Fahrzeugschein) den tatsächlichen Verhältnissen entsprechen, ist der Halter oder der Eigentümer nach § 15 Abs.1 Fahrzeug-Zulassungs-Verordnung (FZV) verpflichtet, diese Änderungen gegen Gebühr eintragen zu lassen.

Wir bitten Sie deshalb, bis spätestens 12.10.2026 die Änderungen eintragen zu lassen. Hierzu haben Sie folgende Unterlagen im Original vorzulegen:

- Zulassungsbescheinigung Teil I (Fahrzeugschein) [required]
- Zulassungsbescheinigung Teil II (Fahrzeugbrief) (nur bei Namensänderung) [not required here]
- gültiger Personalausweis mit neuer Anschrift oder Reisepass [required]
- elektronischer Aufenthaltstitel (eAT) bei Ausländern [required]
- gültige Hauptuntersuchung [required]
- SP-Prüfung [not required here]
- aktuelle Meldebescheinigung [not required here]
- aktualisierte Gewerbeunterlagen [not required here]

Bitte beachten Sie: Wenn Sie dieser Aufforderung nicht innerhalb der genannten Frist nachkommen, müssen wir die Korrektur der Halterdaten durch Einleitung von Zwangsmaßnahmen förmlich erzwingen. Dies ist mit erheblichen Kosten verbunden. Zusätzlich werden wir eine Ordnungswidrigkeitsanzeige mit Bußgeld veranlassen.

Für die Änderung Ihrer Adresse bzw. Ihres Namens fallen Gebühren in Höhe von mindestens 12,30€ an.

Mit freundlichen Grüßen
Im Auftrag
[SIGNATURE] Albrich

## Expected output (target_language: en)

```json
{
  "detected_language": "de",
  "sender": "Stadt Heilbronn, Bürgeramt Kfz-Zulassungsstelle",
  "letter_type": "vehicle registration address update notice",
  "requires_action": true,
  "summary": "The city noticed your registered address on file for your vehicle no longer matches your actual address, and you need to get it corrected.",
  "deadline": { "date": "2026-10-12", "raw_text": "bis spätestens 12.10.2026", "is_relative_to_receipt": false, "confidence": "high" },
  "required_actions": [
    { "action": "Bring your vehicle registration certificate (Part I), a valid ID or passport showing your new address, your residence permit if you're a foreign national, and proof of a valid vehicle inspection, either in person at the registration office or via their online service.", "confidence": "high" }
  ],
  "consequences_if_missed": "The city will formally force the correction through enforcement measures at significant cost to you, and will also file a fine (Ordnungswidrigkeit) against you.",
  "overall_confidence": "high"
}
```

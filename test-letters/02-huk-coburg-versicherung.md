# Test letter 02 — HUK-COBURG, insurance policy copy and account statement

Type: informational, no action required
Language: German

## Input (redacted OCR text)

HUK-COBURG Allgemeine

Ihr Kundendienstbüro:
Yannick Kohl
Frankfurter Str. 34, 74072 Heilbronn
Telefon 07131 6449655 Telefax 0800 2875324814
E-Mail yannick.kohl@hukvm.de

Ihre Kundenbetreuung: Mo–Fr. 8.00–20.00 Uhr, Telefon 09561 96100
Bei Schadenangelegenheiten rund um die Uhr: Telefon 09561 96108

Coburg, 08.07.2026

Herrn
[NAME]
[ADDRESS]

Zweitschrift zum Versicherungsschein - Kraftfahrtversicherung Nr. [POLICY_NUMBER]
bei der HUK-COBURG-Allgemeine Versicherung AG

Grund der Ausfertigung: Änderung des Vertrags: Neue Angaben zu den Tarifierungsmerkmalen - Jährliche Fahrleistung, Kilometerstand

Vertragsdauer: Änderung ab 18.02.2026, 0 Uhr, Ablauf 18.02.2027, 0 Uhr

Versichertes Fahrzeug: Pkw, Ford
Amtliches Kennzeichen: [LICENSE_PLATE]
Leistung, Erstzulassung: 112 kW/152 PS, 11/2021
Fahrzeug-Identifizierungs-Nr.: [VIN]
Kilometerstand, abgelesen: 51.000 km, am 25.05.2026

Versicherungsumfang:
- Kfz-Haftpflichtversicherung Classic-Tarif (100 Mio. € Versicherungssumme): 713,09 €
- mit Schutzbrief: 9,60 €
- Kaskoversicherung ohne Rabattschutz: Vollkasko 500 € SB / Teilkasko 150 € SB: 1.037,08 €
- Fahrerschutz: 23,00 €
- Ausland-Schadenschutz: 9,60 €

Jahresbeitrag: 1.782,77 €

Kontoauszug:
26.05.2026 Vertragsänderung: Belastung 1.782,77 €
26.05.2026 Storno Folgebeitrag: Gutschrift 1.517,74 €
19.06.2026 Zahlungseingang a. Lastschrifteinzug: Gutschrift 265,03 €
06.07.2026 Das Konto ist ausgeglichen: 0,00 €

Wir haben für die Beitragsberechnung aktuelle Vertragsdaten berücksichtigt.

Grundlagen der Beitragsberechnung:
Einstufung: Kfz-Haftpflichtversicherung SF-Klasse 1, Vollkasko SF-Klasse 1
Jährliche Fahrleistung: 14.000 km
Fahrer: Ausschließlich Versicherungsnehmer und Ehepartner
Fahreralter: mindestens 25 Jahre
Nutzung: Überwiegend privat
Versicherungsnehmer Geburtsdatum: [DOB]

Hinweis: Bitte denken Sie daran, dass Sie uns Änderungen zu den Tarifierungsmerkmalen unverzüglich mitteilen müssen.

Zahlungsweise: Jährlich, Zahlungsart: Lastschrift

## Expected output (target_language: en)

```json
{
  "detected_language": "de",
  "sender": "HUK-COBURG Allgemeine Versicherung AG",
  "letter_type": "insurance policy update and account statement",
  "requires_action": false,
  "summary": "This is a copy of your updated car insurance policy reflecting your new mileage and odometer reading, plus a statement showing your account balance is settled at €0.",
  "deadline": { "date": null, "raw_text": null, "is_relative_to_receipt": false, "confidence": "low" },
  "required_actions": [
    { "action": "No immediate action needed, but continue to notify HUK-COBURG promptly whenever your rating details change (e.g. mileage, parking situation, ownership).", "confidence": "medium" }
  ],
  "consequences_if_missed": null,
  "overall_confidence": "high"
}
```

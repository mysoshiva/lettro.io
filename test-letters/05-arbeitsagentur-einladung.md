# Test letter 05 — Bundesagentur für Arbeit, mandatory appointment invitation

Type: fixed-deadline notice with statutory consequence
Language: German

## Input (redacted OCR text)

Bundesagentur für Arbeit
Agentur für Arbeit Heilbronn

Agentur für Arbeit Heilbronn, Rosenbergstr. 50, 74074 Heilbronn

[NAME]
[ADDRESS]

Ihr Zeichen:
Ihre Nachricht:
Mein Zeichen: 121.g
Kundennummer: [CUSTOMER_NUMBER]

Name: Frau Gaidukow
Online: www.arbeitsagentur.de/eservices
Datum: 18. August 2026

Einladung

Guten Tag [NAME],

ich möchte mit Ihnen Ihre aktuelle berufliche Situation besprechen.

Ihre Termindaten:
Datum: Dienstag, den 25. August 2026
Uhrzeit: um 13:00 Uhr
Ort: Agentur für Arbeit Heilbronn, Rosenbergstr. 50, 74074 Heilbronn
Raum: 3. Stock, Zimmer 339

Bitte bringen Sie Ihre Einladung zum Termin mit.

Für Fragen steht Ihnen von Montag - Donnerstag von 08:00 - 18:00 Uhr und am Freitag von 08:00 - 14:00 Uhr folgende Servicerufnummer zur Verfügung: 0800 4 5555 00. Der Anruf ist für Sie gebührenfrei.

Dies ist eine Einladung nach § 309 Abs. 1 Drittes Buch Sozialgesetzbuch (SGB III) in Verbindung mit § 159 SGB III.

Bitte beachten Sie unbedingt die nachfolgenden Rechtsfolgen im Hinblick auf ein mögliches Meldeversäumnis und die weiteren Hinweise.

Unter bestimmten Voraussetzungen können notwendige Reisekosten erstattet werden. Bitte bringen Sie auch Ihren Personalausweis oder Reisepass mit.

Mit freundlichen Grüßen
Ihre Agentur für Arbeit

---

Rechtsfolgenbelehrung, Rechtsbehelfsbelehrung und weitere Hinweise:

Wenn Sie ohne wichtigen Grund dieser Aufforderung nicht nachkommen, tritt eine Sperrzeit ein (Sperrzeit bei Meldeversäumnis; § 159 Abs. 1 Nr. 8 SGB III). Die Sperrzeit dauert eine Woche. Die Sperrzeit beginnt am Tag nach dem versäumten Meldetermin.

Bitte beachten Sie diese Hinweise:
Diese Aufforderung können Sie als hinfällig ansehen,
- wenn Sie sich wegen der Beendigung Ihres Arbeits- oder Ausbildungsverhältnisses arbeitssuchend gemeldet haben (§ 38 Abs. 1 SGB III) und zwischenzeitlich ein neues Arbeitsverhältnis eingegangen sind, so dass Arbeitslosigkeit nicht eintritt.
- wenn Sie Arbeitslosengeld bezogen haben und Ihr Leistungsbezug beendet ist, ein Leistungsanspruch nicht mehr besteht.

Rechtsbehelfsbelehrung: Gegen diese Aufforderung kann jede/r Betroffene oder ein von dieser bevollmächtigter Dritter innerhalb eines Monats nach Bekanntgabe Widerspruch erheben.

---

Response form (page 3):

Der Aufforderung auf Blatt 1 vom 18.08.2026 zur persönlichen Meldung am 25.08.2026 werde ich aus folgenden Gründen nicht nachkommen:
[ ] Ich nehme eine Tätigkeit auf ab ___
[ ] Ich bin ab ___ arbeitsunfähig erkrankt; Arbeitsunfähigkeitsbescheinigung ist beigefügt.
[ ] Ich habe eine Hör-Behinderung und/oder Sprach-Behinderung...
[ ] Sonstiger Grund: ___

## Expected output (target_language: en)

```json
{
  "detected_language": "de",
  "sender": "Bundesagentur für Arbeit, Agentur für Arbeit Heilbronn",
  "letter_type": "mandatory appointment invitation",
  "requires_action": true,
  "summary": "You're being invited to a required in-person appointment to discuss your current job situation. Missing it without a valid reason will suspend your unemployment benefit.",
  "deadline": { "date": "2026-08-25", "raw_text": "Dienstag, den 25. August 2026 um 13:00 Uhr", "is_relative_to_receipt": false, "confidence": "high" },
  "required_actions": [
    { "action": "Attend the appointment on 25 August 2026 at 13:00, at Agentur für Arbeit Heilbronn, Rosenbergstr. 50, room 339 (3rd floor). Bring this invitation letter and your ID or passport.", "confidence": "high" },
    { "action": "If you can't attend — for example, because you already found a job or your claim has already ended — return the enclosed response form explaining why instead.", "confidence": "medium" }
  ],
  "consequences_if_missed": "A one-week suspension of your unemployment benefit eligibility begins the day after the missed appointment, unless you had a valid reason.",
  "overall_confidence": "high"
}
```

Note: the exact exceptions to the appointment requirement are more detailed in the source letter than one line can capture — this is a case where the app should nudge the user to verify with the source rather than answer with full confidence.

# Test letter 04 — Süwag Energie AG, promotional letter

Type: marketing, no action required (negative control)
Language: German

## Input (redacted OCR text)

Süwag
Energie.Besser.Machen

Süwag Vertrieb AG & Co. KG · Postfach 80 05 20 · 65905 Frankfurt am Main

5025 / 12
[NAME]
[ADDRESS]

Frankfurt, im September 2026

Ihr exklusives Energie-Upgrade wartet!

Hallo [NAME],

wir wollen Ihre Energie besser machen und haben deshalb ein Angebot für Sie:
Mehr Leistung ohne zusätzliche Kosten!

Entdecken Sie Ihr individuelles Upgrade zu Ihrer Energielieferung in unserem Online-Service. Dieses exklusive Angebot ist nur für kurze Zeit verfügbar - nutzen Sie die Chance, sich noch mehr Vorteile zu sichern!

Besuchen Sie am Besten direkt unseren Online-Service und sichern Sie sich ganz einfach unter Verträge > Tarif wechseln Ihr Energie-Upgrade: suewag.de/energie-upgrade

Noch nicht registriert? Melden Sie sich unkompliziert für unsere Online-Services an - via Browser oder direkt per App! Es warten nicht nur praktische Funktionen auf Sie, sondern auch attraktive Extras wie unsere 2:1-Gutscheine für Restaurants und Freizeitangebote.

Legen Sie am besten sofort los!

Herzliche Grüße
[SIGNATURE] Christopher Osgood, Geschäftsführer
[SIGNATURE] Toni Walther, Leiter Produkt- und Datenmanagement

## Expected output (target_language: en)

```json
{
  "detected_language": "de",
  "sender": "Süwag Vertrieb AG & Co. KG",
  "letter_type": "promotional offer",
  "requires_action": false,
  "summary": "This is a marketing offer from your energy provider suggesting you can upgrade your plan for no extra cost through their online portal. It's optional — not a request from any authority.",
  "deadline": { "date": null, "raw_text": "nur für kurze Zeit verfügbar", "is_relative_to_receipt": false, "confidence": "low" },
  "required_actions": [],
  "consequences_if_missed": null,
  "overall_confidence": "high"
}
```

Note: this letter is a deliberate negative control — the prompt should confidently report `requires_action: false` here rather than manufacturing an action out of the marketing language.

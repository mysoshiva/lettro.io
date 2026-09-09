# Test letter 03 — Landeshauptstadt Stuttgart, traffic fine witness questionnaire

## Letter text (redacted, original German)

**STUTTGART**

Landeshauptstadt Stuttgart, 70161 Stuttgart

Amt für öffentliche Ordnung
Bußgeldstelle

Auskunft erteilt: Frau Bava, Zi. 320
Telefon: (0711) 216-98702
Telefax: (0711) 216-89909
E-Mail: Bussgeldstelle@stuttgart.de; Ein Rechtsbehelf mit einfacher E-Mail ist nicht möglich.
Internet: www.stuttgart.de
Datum: 19.08.2026
Aktenzeichen: [CASE_NUMBER]

Herrn
[NAME]
[ADDRESS]

Geboren am [DOB] in [PLACE_OF_BIRTH]

**Zeugenfragebogen**

Sehr geehrter Herr [NAME],

der Führerin oder dem Führer des PKW mit dem Kfz-Kennzeichen [LICENSE_PLATE] wird zur Last gelegt, am 21.07.2026 um 15:20 Uhr Stuttgart-Ost B14, Schwanenplatztunnel FR Villastraße Spur Mitte folgende Ordnungswidrigkeit begangen zu haben:

> Sie überschritten die zulässige Höchstgeschwindigkeit außerhalb geschlossener Ortschaften um 8 km/h.
> Zulässige Geschwindigkeit: 40 km/h.
> Festgestellte Geschwindigkeit (nach Toleranzabzug): 48 km/h.
> § 41 Abs. 1 iVm Anlage 2, § 49 StVO; § 24 Abs. 1, 3 Nr. 5 StVG; 11.3.1 BKat

Beweismittel: Foto, Gemessen mit TraffiStar S330, Film/Bild-Nr. [PHOTO_NUMBER], Sensormessung und Foto

Die Toleranz beträgt 3 km/h

Im Zuge der Ermittlungen werden Sie als Zeugin oder Zeuge gehört und gebeten, die Personalien der verantwortlichen Person (auch die Geburtsdaten) und die Anschrift auf dem Antwortbogen mitzuteilen.

Bitte senden Sie den Fragebogen innerhalb einer Woche nach Zugang dieses Schreibens an die oben genannte Dienststelle zurück, selbst wenn Sie von Ihrem Zeugnis-/Aussageverweigerungsrecht Gebrauch machen. Sie vermeiden dadurch weitere Ermittlungen.

Auf die Rücksendung des Fragebogens kann verzichtet werden, wenn das angebotene Verwarnungsgeld (abzüglich bereits geleisteter Zahlungen)

> in Höhe von 20,00 €

innerhalb einer Woche ab Zugang dieses Schreibens gezahlt wird.

**Benachrichtigung über die Verarbeitung Ihrer personenbezogenen Daten**

Die Datenverarbeitung erfolgt zu Zwecken der Verfolgung und Ahndung der Ordnungswidrigkeiten unter Beachtung des § 500 der Strafprozeßordnung (StPO) i.V.m. § 46 des Gesetzes über Ordnungswidrigkeiten (OWiG), des Bundesdatenschutzgesetzes (BDSG) sowie Landesdatenschutzgesetz (LDSG-JB).

**ePayment Portal Details:**
Website: https://anhoerung.stuttgart.de
Login: [LOGIN_ID]
PIN: [PIN]

## Expected output (target_language: en)

```json
{
  "detected_language": "de",
  "sender": "Landeshauptstadt Stuttgart, Amt für öffentliche Ordnung, Bußgeldstelle",
  "letter_type": "traffic fine witness questionnaire",
  "requires_action": true,
  "summary": "Your registered vehicle was caught speeding. As the owner, you're asked to either name the driver on the enclosed form, or simply pay a €20 fine to close the matter without further questioning.",
  "deadline": {
    "date": null,
    "raw_text": "innerhalb einer Woche ab Zugang dieses Schreibens",
    "is_relative_to_receipt": true,
    "confidence": "high"
  },
  "required_actions": [
    {
      "action": "Either return the completed witness questionnaire identifying the driver, or pay the €20 fine (Verwarnungsgeld), within one week of the day you actually received this letter.",
      "confidence": "high"
    }
  ],
  "consequences_if_missed": "If you neither respond nor pay, the authority will pursue further investigation.",
  "overall_confidence": "high"
}
```

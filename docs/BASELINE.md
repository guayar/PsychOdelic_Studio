# Baseline produkcji „Once Upon a Garden” (zabezpieczenie przed zmianą)

Cel: udowodnić, że pipeline produkcyjny nie został zmieniony przez Studio. Nic w tym dokumencie nie modyfikuje plików.

## Co zapisać przed pierwszą zmianą (u Ciebie, tylko odczyt)

```bash
OUG="/media/sututrang/New 11/teledysk/Psychedelic/Once Upon a Garden"
cd "$OUG"
find _docs _PLAN -type f -print0 | sort -z | xargs -0 sha256sum > ~/oug_baseline_$(date +%Y%m%d).sha256
```

Plik `oug_baseline_*.sha256` przechowaj poza projektem. Po każdej sesji Studio porównaj:

```bash
cd "$OUG" && sha256sum -c ~/oug_baseline_YYYYMMDD.sha256
```

Każda różnica oznacza zmianę produkcyjnych plików: zatrzymaj się i wyjaśnij.

## Stan

- Baseline jeszcze nie został wykonany (brak dostępu do Twojego dysku z tej sesji).
- Plików `_docs/*` i `_PLAN/*` nie widziałem.
- Wykonanie renderu w ramach baseline'u nie jest potrzebne ani zalecane.

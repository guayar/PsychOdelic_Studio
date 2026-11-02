"""Instalator studia: wykrywa ComfyUI, kopiuje workflowy, raportuje brakujace nody i wagi.

Zasady (z briefu uzytkownika):
  * NIE pobiera wag modeli.
  * NIE instaluje custom nodes ani niczego do ComfyUI poza plikami workflow.
  * NIE nadpisuje istniejacych plikow w ComfyUI (konflikt -> zapis obok jako *.studio.json).
  * Kazdy brak jest opisany: co to jest, skad wziac (repozytorium lub nazwa wagi), gdzie to wrzucic.
"""

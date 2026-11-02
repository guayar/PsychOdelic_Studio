export const fmtBytes = (b: number) => `${(b / 1024 ** 3).toFixed(1)} GiB`;
export const fmtSeconds = (s: number) => `${s.toFixed(2)} s`;
export const stateLabel: Record<string, string> = {
  PLAN_READY: "plan gotowy", PREPARED: "przygotowane", DIRECTOR_UNLOADING: "zwalnianie Directora",
  GPU_FREE_VERIFIED: "GPU wolne", RENDER_QUEUED: "w kolejce", RENDERING: "renderowanie",
  OUTPUT_VALIDATING: "sprawdzanie wyniku", POSTPROCESSING: "postprocessing",
  AWAITING_USER_REVIEW: "czeka na Twoją ocenę", ACCEPTED: "zaakceptowane", REJECTED: "odrzucone",
  DIRECTOR_RELOAD_PENDING: "ładowanie Directora", DIRECTOR_READY: "gotowe", FAILED: "błąd",
  CANCELLED: "anulowane", RECOVERING: "odzyskiwanie", GPU_BUSY: "GPU zajęte",
  CAPABILITY_UNAVAILABLE: "niedostępne",
};
export const kindLabel: Record<string, string> = { h3_extend: "H3 Extender", ltx_lip: "LTX lipsync" };

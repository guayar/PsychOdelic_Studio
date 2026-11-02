import type { Key } from "./i18n";
export const fmtBytes = (b: number) => `${(b / 1024 ** 3).toFixed(1)} GiB`;
export const stateKey = (state: string): Key => `state.${state}` as Key;
export const kindKey = (kind: string): Key => `kind.${kind}` as Key;

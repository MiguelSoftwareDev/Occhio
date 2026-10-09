export const time = (value?: string) =>
  value
    ? new Date(value).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "—";
export const percent = (value?: number) =>
  value === undefined
    ? "—"
    : value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

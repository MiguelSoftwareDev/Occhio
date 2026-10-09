import { useCallback, useEffect, useRef, useState } from "react";
import { request } from "../lib/api";

// Atualiza sem sobrepor requisições
export function usePolling<T>(path: string, interval: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [updated, setUpdated] = useState<number | null>(null);
  const [revision, setRevision] = useState(0);
  const current = useRef(0);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const id = ++current.current;
    async function poll() {
      try {
        const result = await request<T>(path, { signal: controller.signal });
        if (active && id === current.current) {
          setData(result);
          setError("");
          setUpdated(Date.now());
        }
      } catch (err) {
        if (active)
          setError(err instanceof Error ? err.message : "Falha de conexão");
      } finally {
        if (active) timer = setTimeout(poll, interval);
      }
    }
    setData(null);
    setUpdated(null);
    void poll();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [path, interval, revision]);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  return { data, error, updated, refresh };
}

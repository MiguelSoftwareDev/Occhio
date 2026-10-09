import { useEffect, useRef } from "react";
import { X, HardDrive } from "lucide-react";
import { usePolling } from "../hooks/usePolling";
import { memorySize } from "./ProcessRadar";
type Volume = {
  device: string;
  mountpoint: string;
  filesystem: string;
  available: boolean;
  total_bytes?: number;
  used_bytes?: number;
  free_bytes?: number;
  percent?: number;
  error?: string;
};
export function StorageDialog({ close }: { close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { data, error } = usePolling<{ volumes: Volume[] }>("/disks", 5000);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      onCancel={close}
      aria-labelledby="storage-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div className="dialog-head">
        <h2 id="storage-title">Armazenamento</h2>
        <button
          className="icon-button"
          aria-label="Fechar discos"
          onClick={close}
        >
          <X />
        </button>
      </div>
      <p>
        Volumes montados no computador monitorado. Um disco físico pode conter
        várias partições; HD/SSD não é inferido pelo nome.
      </p>
      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Consultando volumes…</p>}
      {data?.volumes.length === 0 && (
        <p>Nenhum volume acessível neste ambiente.</p>
      )}
      {data?.volumes.map((v) => (
        <article className="disk-volume" key={`${v.device}:${v.mountpoint}`}>
          <h3>
            <HardDrive size={20} /> {v.mountpoint}
          </h3>
          <p>
            {v.device} · {v.filesystem}
          </p>
          {v.available ? (
            <>
              <strong>
                {memorySize(v.used_bytes!)} de {memorySize(v.total_bytes!)} ·{" "}
                {v.percent?.toFixed(1)}%
              </strong>
              <div className="meter">
                <i style={{ width: `${v.percent}%` }} />
              </div>
              <small>{memorySize(v.free_bytes!)} livres</small>
            </>
          ) : (
            <p>{v.error}</p>
          )}
        </article>
      ))}
    </dialog>
  );
}

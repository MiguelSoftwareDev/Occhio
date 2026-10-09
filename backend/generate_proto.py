from pathlib import Path

from grpc_tools import protoc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTO_DIR = PROJECT_ROOT / "proto"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "generated"


# Gera os módulos Python do contrato
def generate() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={OUTPUT_DIR}",
            f"--grpc_python_out={OUTPUT_DIR}",
            str(PROTO_DIR / "system_monitor.proto"),
        ]
    )
    if result != 0:
        raise SystemExit(result)
    grpc_file = OUTPUT_DIR / "system_monitor_pb2_grpc.py"
    grpc_file.write_text(
        grpc_file.read_text().replace(
            "import system_monitor_pb2 as", "from . import system_monitor_pb2 as"
        )
    )
    (OUTPUT_DIR / "__init__.py").touch(exist_ok=True)


if __name__ == "__main__":
    generate()

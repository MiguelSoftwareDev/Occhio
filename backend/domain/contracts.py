from google.protobuf.json_format import MessageToDict

from backend.generated import system_monitor_pb2
from backend.generated import system_monitor_pb2_grpc as system_monitor_pb2_grpc


# Converte métricas para Protocol Buffers
def snapshot_to_message(snapshot: dict) -> system_monitor_pb2.SystemSnapshot:
    return system_monitor_pb2.SystemSnapshot(**snapshot)


# Converte Protocol Buffers para métricas
def message_to_snapshot(message: system_monitor_pb2.SystemSnapshot) -> dict:
    return {
        "host_name": message.host_name,
        "captured_at": message.captured_at,
        "cpu_percent": message.cpu_percent,
        "memory_percent": message.memory_percent,
        "memory_used_bytes": message.memory_used_bytes,
        "memory_total_bytes": message.memory_total_bytes,
        "disk_percent": message.disk_percent,
        "process_count": message.process_count,
        "uptime_seconds": message.uptime_seconds,
        "top_processes": [
            {
                "pid": item.pid,
                "name": item.name,
                "cpu_percent": item.cpu_percent,
                "memory_bytes": item.memory_bytes,
                "memory_percent": item.memory_percent,
                "cpu_measured": item.cpu_measured,
            }
            for item in message.top_processes
        ],
    }


# Converte a resposta gRPC para JSON
def result_to_dict(result: system_monitor_pb2.AnalysisResult) -> dict:
    return MessageToDict(
        result, preserving_proto_field_name=True, always_print_fields_with_no_presence=True
    )

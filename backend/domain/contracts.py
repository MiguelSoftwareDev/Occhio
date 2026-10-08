from google.protobuf.json_format import MessageToDict

from backend.generated import system_monitor_pb2
from backend.generated import system_monitor_pb2_grpc as system_monitor_pb2_grpc


# Converte métricas para Protocol Buffers || Convert metrics to Protocol Buffers
def snapshot_to_message(snapshot: dict) -> system_monitor_pb2.SystemSnapshot:
    return system_monitor_pb2.SystemSnapshot(**snapshot)


# Converte Protocol Buffers para métricas || Convert Protocol Buffers to metrics
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
    }


# Converte a resposta gRPC para JSON || Convert the gRPC response to JSON
def result_to_dict(result: system_monitor_pb2.AnalysisResult) -> dict:
    return MessageToDict(
        result, preserving_proto_field_name=True, always_print_fields_with_no_presence=True
    )

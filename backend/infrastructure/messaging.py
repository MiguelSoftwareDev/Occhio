import json

import pika

from backend.core.config import SETTINGS

EXCHANGE_NAME = "occhio.events"
QUEUE_NAME = "analysis.results.v2"
DEAD_QUEUE = "analysis.failed.v2"
ROUTING_KEY = "system.analysis"


# Abre a conexão com o broker || Open the broker connection
def open_connection() -> pika.BlockingConnection:
    parameters = pika.URLParameters(SETTINGS.rabbitmq_url)
    parameters.connection_attempts = 2
    parameters.retry_delay = 1
    parameters.socket_timeout = 3
    parameters.stack_timeout = 6
    parameters.blocked_connection_timeout = 5
    parameters.heartbeat = 30
    return pika.BlockingConnection(parameters)


# Declara a topologia durável || Declare the durable topology
def prepare_queue(channel):
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.queue_declare(queue=DEAD_QUEUE, durable=True)
    queue = channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={"x-dead-letter-exchange": "", "x-dead-letter-routing-key": DEAD_QUEUE},
    )
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)
    return queue


# Publica com confirmação do broker || Publish with broker confirmation
def publish_result(result: dict) -> None:
    connection = open_connection()
    try:
        channel = connection.channel()
        prepare_queue(channel)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            mandatory=True,
            body=json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=result["analysis_id"],
                type="system.analysis.v1",
            ),
        )
    finally:
        if connection.is_open:
            connection.close()


# Consulta filas e consumidores || Check queues and consumers
def get_broker_status() -> dict:
    connection = open_connection()
    try:
        channel = connection.channel()
        queue = prepare_queue(channel)
        dead = channel.queue_declare(queue=DEAD_QUEUE, passive=True)
        return {
            "available": True,
            "queued_messages": queue.method.message_count,
            "consumers": queue.method.consumer_count,
            "failed_messages": dead.method.message_count,
        }
    finally:
        if connection.is_open:
            connection.close()

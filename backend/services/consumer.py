import json
import logging
import sqlite3
import time

import pika
from pydantic import ValidationError

from backend.infrastructure.messaging import QUEUE_NAME, open_connection, prepare_queue
from backend.infrastructure.storage import initialize_database, save_result

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("occhio.consumer")


# Confirma apenas depois da persistência || Acknowledge only after persistence
def handle_message(channel, method, properties, body) -> None:
    try:
        save_result(json.loads(body.decode("utf-8")))
    except (ValueError, UnicodeError, ValidationError, TypeError):
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logger.warning("Mensagem inválida enviada à fila de falhas")
    except sqlite3.Error:
        # Fecha a conexão para devolver a mensagem sem confirmação || Requeue on disconnect
        raise
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Resultado consumido: %s", properties.message_id)


# Reconecta com espera progressiva || Reconnect with backoff
def consume() -> None:
    delay = 1
    while True:
        connection = None
        try:
            initialize_database()
            connection = open_connection()
            channel = connection.channel()
            prepare_queue(channel)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME, on_message_callback=handle_message, auto_ack=False
            )
            logger.info("Consumidor ativo: %s", QUEUE_NAME)
            delay = 1
            channel.start_consuming()
        except (pika.exceptions.AMQPError, OSError, sqlite3.Error) as error:
            logger.warning(
                "Consumidor indisponível (%s); nova tentativa em %ss", type(error).__name__, delay
            )
        finally:
            if connection and connection.is_open:
                try:
                    connection.close()
                except pika.exceptions.AMQPError:
                    pass
        time.sleep(delay)
        delay = min(delay * 2, 30)


if __name__ == "__main__":
    try:
        consume()
    except KeyboardInterrupt:
        logger.info("Consumidor encerrado")

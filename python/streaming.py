"""
Real-Time Fraud Detection Streaming with Kafka
===============================================
Kafka producer and consumer for real-time fraud detection.

Features:
- Transaction ingestion
- Real-time fraud detection
- Alert generation
- Stream processing with dead-letter queue (DLQ) for poison pills

Author: SentinAL Team
Date: 2026-01-24
"""

import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

# Maximum times a message is retried before being sent to the DLQ.
# Prevents a single malformed message from blocking the consumer forever.
MAX_RETRIES = 3


class FraudDetectionProducer:
    """
    Kafka producer for transaction ingestion.

    Uses fire-and-forget with an error callback instead of blocking
    future.get(), which was a synchronous bottleneck limiting throughput.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9093"):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka broker address
        """
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",  # Wait for all replicas to acknowledge
            retries=3,
            max_in_flight_requests_per_connection=1,  # Ensure ordering
        )

        self.topic = "transactions"
        logger.info(f"Kafka producer initialized for topic: {self.topic}")

    def send_transaction(self, transaction: Dict[str, Any], user_id: Optional[str] = None):
        """
        Send transaction to Kafka asynchronously (fire-and-forget with error callback).

        Fix: Replaced blocking future.get(timeout=10) with an on_error callback.
        This keeps ingestion asynchronous and prevents a single slow broker
        acknowledgement from stalling the caller for up to 10 seconds.

        Args:
            transaction: Transaction data
            user_id: Optional user ID for partitioning
        """
        # Stamp metadata before sending
        transaction["timestamp"] = transaction.get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )
        transaction["ingestion_time"] = datetime.now(timezone.utc).isoformat()

        def _on_send_success(record_metadata):
            logger.debug(
                f"Transaction sent: topic={record_metadata.topic} "
                f"partition={record_metadata.partition} "
                f"offset={record_metadata.offset}"
            )

        def _on_send_error(exc):
            logger.error(f"Failed to send transaction for user={user_id}: {exc}")

        # Non-blocking — attach callbacks instead of blocking on future.get()
        self.producer.send(
            self.topic, key=user_id, value=transaction
        ).add_callback(_on_send_success).add_errback(_on_send_error)

    def close(self):
        """Flush all pending messages and close the producer."""
        self.producer.flush()
        self.producer.close()


class FraudDetectionConsumer:
    """
    Kafka consumer for real-time fraud detection.

    Poison-pill fix: tracks a per-message retry counter and routes
    persistently failing messages to a dead-letter topic instead of
    re-processing them forever (which previously blocked new messages).
    """

    def __init__(
        self, bootstrap_servers: str = "localhost:9093", group_id: str = "fraud-detection-group"
    ):
        """
        Initialize Kafka consumer.

        Args:
            bootstrap_servers: Kafka broker address
            group_id: Consumer group ID
        """
        self.consumer = KafkaConsumer(
            "transactions",
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            enable_auto_commit=False,  # Manual commit — prevents message loss on crash
        )

        # Alert producer (fraud alerts)
        self.alert_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        self.alert_topic = "fraud-alerts"
        self.dlq_topic = "transactions-dlq"  # Dead-letter queue for poison pills

        # In-memory retry counter keyed by (partition, offset)
        self._retry_counts: Dict[tuple, int] = {}

        logger.info(f"Kafka consumer initialized for group: {group_id}")

    def process_stream(self, fraud_detector: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Process transaction stream with poison-pill protection via DLQ.

        If a message fails MAX_RETRIES times it is published to the
        dead-letter topic and the offset is committed so the consumer
        moves forward instead of looping forever.

        Args:
            fraud_detector: Function that takes a transaction dict and
                            returns a fraud analysis dict
        """
        logger.info("Starting stream processing...")

        try:
            for message in self.consumer:
                msg_key = (message.partition, message.offset)
                transaction = message.value
                user_id = message.key

                logger.info(f"Processing transaction for user: {user_id}")

                try:
                    result = fraud_detector(transaction)

                    if result.get("is_fraud", False):
                        self._send_alert(user_id, transaction, result)

                    logger.info(
                        f"Fraud probability: {result.get('fraud_probability', 0):.2f}"
                    )

                    # Commit only after successful processing
                    self.consumer.commit()
                    # Clear retry counter on success
                    self._retry_counts.pop(msg_key, None)

                except Exception as e:
                    retry_count = self._retry_counts.get(msg_key, 0) + 1
                    self._retry_counts[msg_key] = retry_count

                    logger.error(
                        f"Error processing transaction (attempt {retry_count}/{MAX_RETRIES}): {e}"
                    )

                    if retry_count >= MAX_RETRIES:
                        # Poison pill — route to DLQ and move on
                        logger.warning(
                            f"Message at partition={message.partition} offset={message.offset} "
                            f"exceeded {MAX_RETRIES} retries. Sending to DLQ: {self.dlq_topic}"
                        )
                        self._send_to_dlq(user_id, transaction, str(e))
                        self.consumer.commit()  # Commit so consumer advances past it
                        self._retry_counts.pop(msg_key, None)
                    # Otherwise: do NOT commit → message will be reprocessed on next poll

        except KeyboardInterrupt:
            logger.info("Stream processing stopped by user")
        finally:
            self.close()

    def _send_alert(self, user_id: str, transaction: Dict[str, Any], result: Dict[str, Any]):
        """Send fraud alert to the alerts topic."""
        alert = {
            "user_id": user_id,
            "transaction": transaction,
            "fraud_probability": result.get("fraud_probability"),
            "risk_level": result.get("risk_level"),
            "reason": result.get("reason"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": "real_time_fraud_detection",
        }

        self.alert_producer.send(self.alert_topic, value=alert)
        # Flush ensures the alert reaches Kafka before we ack the source message
        self.alert_producer.flush(timeout=5)
        logger.warning(
            f"FRAUD ALERT: User {user_id}, "
            f"probability={result.get('fraud_probability', 0):.2f}"
        )

    def _send_to_dlq(self, user_id: Optional[str], transaction: Dict[str, Any], error: str):
        """
        Route a poison pill message to the dead-letter topic.

        DLQ messages include the original payload plus failure metadata
        so they can be inspected and replayed manually if needed.
        """
        dlq_payload = {
            "original_transaction": transaction,
            "user_id": user_id,
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "retries": MAX_RETRIES,
        }
        try:
            self.alert_producer.send(self.dlq_topic, value=dlq_payload)
            self.alert_producer.flush(timeout=5)
        except Exception as dlq_exc:
            # If even the DLQ send fails, log and continue — don't block the consumer
            logger.error(f"Failed to send message to DLQ: {dlq_exc}")

    def close(self):
        """Close consumer and alert producer."""
        self.consumer.close()
        self.alert_producer.close()


# Example usage
if __name__ == "__main__":
    # Send a test transaction
    producer = FraudDetectionProducer()

    transaction = {
        "user_id": "77",
        "amount": 5000,
        "merchant": "Online Store",
        "location": "New York",
    }

    producer.send_transaction(transaction, user_id="77")
    producer.close()

    # Consume and process
    def simple_fraud_detector(txn):
        amount = txn.get("amount", 0)
        is_fraud = amount > 10000
        return {
            "is_fraud": is_fraud,
            "fraud_probability": 0.9 if is_fraud else 0.1,
            "risk_level": "high" if is_fraud else "low",
            "reason": "High amount" if is_fraud else "Normal",
        }

    consumer = FraudDetectionConsumer()
    consumer.process_stream(simple_fraud_detector)

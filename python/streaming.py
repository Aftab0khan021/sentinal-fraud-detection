"""
Real-Time Fraud Detection Streaming with Kafka
===============================================
Kafka producer and consumer for real-time fraud detection.

Features:
- Transaction ingestion
- Real-time fraud detection
- Alert generation
- Stream processing

Author: SentinAL Team
Date: 2026-01-24
"""

import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class FraudDetectionProducer:
    """
    Kafka producer for transaction ingestion.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9093"):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker address
        """
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1  # Ensure ordering
        )
        
        self.topic = "transactions"
        logger.info(f"Kafka producer initialized for topic: {self.topic}")
    
    def send_transaction(self, transaction: Dict[str, Any], user_id: Optional[str] = None):
        """
        Send transaction to Kafka.
        
        Args:
            transaction: Transaction data
            user_id: Optional user ID for partitioning
        """
        # Add metadata
        transaction["timestamp"] = transaction.get("timestamp", datetime.utcnow().isoformat())
        transaction["ingestion_time"] = datetime.utcnow().isoformat()
        
        # Send to Kafka
        future = self.producer.send(
            self.topic,
            key=user_id,
            value=transaction
        )
        
        try:
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            logger.info(f"Transaction sent: partition={record_metadata.partition}, offset={record_metadata.offset}")
        except KafkaError as e:
            logger.error(f"Failed to send transaction: {e}")
            raise
    
    def close(self):
        """Close producer"""
        self.producer.flush()
        self.producer.close()


class FraudDetectionConsumer:
    """
    Kafka consumer for real-time fraud detection.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9093",
        group_id: str = "fraud-detection-group"
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
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # Bug #17: manual commit prevents message loss on crash
        )
        
        # Alert producer
        self.alert_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.alert_topic = "fraud-alerts"
        logger.info(f"Kafka consumer initialized for group: {group_id}")
    
    def process_stream(self, fraud_detector: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Process transaction stream.
        
        Args:
            fraud_detector: Function that takes transaction and returns fraud analysis
        """
        logger.info("Starting stream processing...")
        
        try:
            for message in self.consumer:
                transaction = message.value
                user_id = message.key
                
                logger.info(f"Processing transaction for user: {user_id}")
                
                try:
                    # Detect fraud
                    result = fraud_detector(transaction)

                    # If fraud detected, send alert
                    if result.get("is_fraud", False):
                        self._send_alert(user_id, transaction, result)

                    # Log result
                    logger.info(f"Fraud probability: {result.get('fraud_probability', 0):.2f}")

                    # Bug #17: Only commit offset after successful processing
                    self.consumer.commit()

                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    # Do NOT commit — message will be reprocessed on next start
        
        except KeyboardInterrupt:
            logger.info("Stream processing stopped by user")
        finally:
            self.close()
    
    def _send_alert(self, user_id: str, transaction: Dict[str, Any], result: Dict[str, Any]):
        """
        Send fraud alert.
        
        Args:
            user_id: User ID
            transaction: Original transaction
            result: Fraud detection result
        """
        alert = {
            "user_id": user_id,
            "transaction": transaction,
            "fraud_probability": result.get("fraud_probability"),
            "risk_level": result.get("risk_level"),
            "reason": result.get("reason"),
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "real_time_fraud_detection"
        }
        
        self.alert_producer.send(self.alert_topic, value=alert)
        # Bug #24: flush ensures the alert is actually sent and not silently dropped
        self.alert_producer.flush(timeout=5)
        logger.warning(f"FRAUD ALERT: User {user_id}, probability={result.get('fraud_probability'):.2f}")
    
    def close(self):
        """Close consumer and producer"""
        self.consumer.close()
        self.alert_producer.close()


# Example usage
if __name__ == "__main__":
    # Example: Send transactions
    producer = FraudDetectionProducer()
    
    transaction = {
        "user_id": "77",
        "amount": 5000,
        "merchant": "Online Store",
        "location": "New York"
    }
    
    producer.send_transaction(transaction, user_id="77")
    producer.close()
    
    # Example: Consume and process
    def simple_fraud_detector(transaction):
        # Simple rule: amounts > 10000 are suspicious
        amount = transaction.get("amount", 0)
        is_fraud = amount > 10000
        
        return {
            "is_fraud": is_fraud,
            "fraud_probability": 0.9 if is_fraud else 0.1,
            "risk_level": "high" if is_fraud else "low",
            "reason": "High amount" if is_fraud else "Normal"
        }
    
    consumer = FraudDetectionConsumer()
    consumer.process_stream(simple_fraud_detector)

"""
Shared Event Bus module for RabbitMQ integration.
Provides publish_event() and EventConsumer for asynchronous messaging between services.
"""
import json
import logging
import time
import pika

logger = logging.getLogger(__name__)

RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
EXCHANGE_NAME = 'bookstore_events'


def get_connection(retries=5, delay=5):
    """Create a connection to RabbitMQ with retry logic."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    for attempt in range(retries):
        try:
            connection = pika.BlockingConnection(parameters)
            logger.info("Connected to RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"RabbitMQ connection attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def publish_event(event_type, data):
    """
    Publish an event to the RabbitMQ exchange.
    
    Args:
        event_type: String identifying the event (e.g., 'order.created', 'payment.reserved')
        data: Dictionary with event payload
    """
    try:
        connection = get_connection()
        channel = connection.channel()
        
        # Declare a topic exchange
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='topic',
            durable=True,
        )
        
        message = json.dumps({
            'event_type': event_type,
            'data': data,
            'timestamp': time.time(),
        })
        
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=event_type,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json',
            ),
        )
        
        logger.info(f"Published event: {event_type}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        return False


class EventConsumer:
    """
    Consume events from RabbitMQ.
    
    Usage:
        consumer = EventConsumer('my-service-queue', ['order.created', 'payment.#'])
        consumer.register_handler('order.created', handle_order_created)
        consumer.start()
    """
    
    def __init__(self, queue_name, routing_keys):
        self.queue_name = queue_name
        self.routing_keys = routing_keys
        self.handlers = {}
    
    def register_handler(self, event_type, handler_func):
        """Register a handler function for a specific event type."""
        self.handlers[event_type] = handler_func
    
    def _callback(self, channel, method, properties, body):
        """Internal callback for processing received messages."""
        try:
            message = json.loads(body)
            event_type = message.get('event_type', '')
            data = message.get('data', {})
            
            logger.info(f"Received event: {event_type}")
            
            handler = self.handlers.get(event_type)
            if handler:
                handler(data)
                logger.info(f"Processed event: {event_type}")
            else:
                logger.warning(f"No handler registered for event: {event_type}")
            
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start(self):
        """Start consuming events. This is a blocking call."""
        connection = get_connection()
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='topic',
            durable=True,
        )
        
        # Declare queue
        channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Bind queue to exchange with routing keys
        for key in self.routing_keys:
            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=self.queue_name,
                routing_key=key,
            )
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback)
        
        logger.info(f"Started consuming on queue: {self.queue_name}")
        channel.start_consuming()

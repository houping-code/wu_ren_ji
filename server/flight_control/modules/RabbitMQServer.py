import queue
import time
import pika
import threading


class RabbitMQServer:
    def __init__(self, host, port, userName, password, service_type, message_ttl=10000, max_retries=3):
        self.host = host
        self.port = port
        self.userName = userName
        self.password = password
        self.service_type = service_type
        self.message_ttl = message_ttl
        self.max_retries = max_retries

        # 初始化连接
        self.credentials = pika.PlainCredentials(self.userName, self.password)
        self.init_send_connection()
        self.init_receive_connection()

        # 创建消息队列
        self.message_queue = queue.Queue()

        # 启动发送线程
        self.running = True
        self.send_thread = threading.Thread(target=self._process_message_queue)
        self.send_thread.daemon = True
        self.send_thread.start()

    def create_connection(self):
        # 创建连接,添加心跳检测
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=self.credentials,
                heartbeat=60,  # 添加心跳检测
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5
            )
        )

    def init_send_connection(self):
        if hasattr(self, 'sendConnection') and self.sendConnection.is_open:
            try:
                self.sendConnection.close()
            except:
                pass

        self.sendConnection = self.create_connection()
        self.sendChannel = self.sendConnection.channel()
        self.sendChannel.exchange_declare(exchange='server_to_client', exchange_type='direct')

    def init_receive_connection(self):
        if hasattr(self, 'receiveConnection') and self.receiveConnection.is_open:
            try:
                self.receiveConnection.close()
            except:
                pass

        self.receiveConnection = self.create_connection()
        self.receiveChannel = self.receiveConnection.channel()

        self.receiveChannel.exchange_declare(exchange='client_to_server', exchange_type='topic')

        arguments = {'x-message-ttl': self.message_ttl}
        result = self.receiveChannel.queue_declare(queue='', exclusive=True, arguments=arguments)
        self.queue_name = result.method.queue

        self.receiveChannel.queue_bind(
            exchange='client_to_server',
            queue=self.queue_name,
            routing_key=f"{self.service_type}"
        )

    def send(self, client_name, message):
        # 将消息放入队列
        self.message_queue.put((client_name, message))

    def _send_message(self, client_name, message):
        routing_key = f'{client_name}'
        for retry in range(self.max_retries):
            try:
                self.sendChannel.basic_publish(
                    exchange='server_to_client',
                    routing_key=routing_key,
                    body=message
                )
                print(f" [x] Sent to {client_name}: {message}")
                return
            except Exception:
                print(f"Send connection lost, reconnecting {retry + 1}/{self.max_retries}")
                try:
                    # 重新建立连接，发送消息
                    self.init_send_connection()
                    self.sendChannel.basic_publish(
                        exchange='server_to_client',
                        routing_key=routing_key,
                        body=message
                    )
                    return
                except Exception:
                    print(f"Failed to reconnect send connection")
                    if retry == self.max_retries - 1:
                        raise
                    time.sleep(1)

    def _process_message_queue(self):
        while self.running:
            try:
                # 从队列中获取消息
                client_name, message = self.message_queue.get(timeout=1)
                self._send_message(client_name, message)
            except queue.Empty:
                # 队列为空时继续循环
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
                time.sleep(1)

    def receive(self, callback):
        # 开始消费消息
        for retry in range(self.max_retries):
            try:
                self.receiveChannel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
                self.receiveChannel.start_consuming()
            except Exception:
                print(f"Receive connection lost, reconnecting {retry + 1}/{self.max_retries}")
                try:
                    # 重新建立连接，接收消息
                    self.init_receive_connection()
                    self.receiveChannel.basic_consume(queue=self.queue_name, on_message_callback=callback,
                                                      auto_ack=True)
                    self.receiveChannel.start_consuming()
                except Exception:
                    print(f"Failed to reconnect receive connection")
                    if retry == self.max_retries - 1:
                        raise
                    time.sleep(2)

    def close(self):
        self.running = False
        self.sendChannel.close()
        self.receiveChannel.close()

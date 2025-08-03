import time
import pika


class RabbitMQClient:
    def __init__(self, host, port, client_name, userName, password, message_ttl=10000, max_retries=3):
        self.host = host
        self.port = port
        self.client_name = client_name
        self.userName = userName
        self.password = password
        self.message_ttl = message_ttl
        self.max_retries = max_retries
        self.credentials = pika.PlainCredentials(self.userName, self.password)
        self.init_send_connection()
        self.init_receive_connection()

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
        self.sendChannel.exchange_declare(exchange='client_to_server', exchange_type='topic')

    def init_receive_connection(self):
        if hasattr(self, 'receiveConnection') and self.receiveConnection.is_open:
            try:
                self.receiveConnection.close()
            except:
                pass

        self.receiveConnection = self.create_connection()
        self.receiveChannel = self.receiveConnection.channel()

        self.receiveChannel.exchange_declare(exchange='server_to_client', exchange_type='direct')

        arguments = {
            'x-client_message-ttl': self.message_ttl
        }
        result = self.receiveChannel.queue_declare(queue='', exclusive=True, arguments=arguments)
        self.queue_name = result.method.queue

        self.receiveChannel.queue_bind(exchange='server_to_client', queue=self.queue_name,
                                       routing_key=f'{self.client_name}')

    def send(self, service_type, data):
        routing_key = f'{service_type}'

        for retry in range(self.max_retries):
            try:
                self.sendChannel.basic_publish(exchange='client_to_server', routing_key=routing_key, body=data)
                return
            except:
                print(f"Send connection lost, reconnecting {retry + 1}/{self.max_retries}")
                try:
                    # 重新建立连接，发送消息
                    self.init_send_connection()
                    self.sendChannel.basic_publish(exchange='client_to_server', routing_key=routing_key, body=data)
                    return
                except:
                    print(f"Failed to reconnect send connection")
                    if retry == self.max_retries - 1:
                        raise
                    time.sleep(2)

    def receive(self, callback):
        # 开始消费消息
        for retry in range(self.max_retries):
            try:
                self.receiveChannel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
                self.receiveChannel.start_consuming()
            except:
                print(f"Receive connection lost, reconnecting {retry + 1}/{self.max_retries}")
                try:
                    # 重新建立连接，接收消息
                    self.init_receive_connection()
                    self.receiveChannel.basic_consume(queue=self.queue_name, on_message_callback=callback,
                                                      auto_ack=True)
                    self.receiveChannel.start_consuming()
                except:
                    print(f"Failed to reconnect receive connection")
                    if retry == self.max_retries - 1:
                        raise
                    time.sleep(2)

    def close(self):
        self.sendChannel.close()
        self.receiveChannel.close()

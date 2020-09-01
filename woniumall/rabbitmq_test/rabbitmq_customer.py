"""
    @Time    : 2020/9/1 11:21 
    @Author  : fate
    @Site    : 
    @File    : rabbitmq_customer.py
    @Software: PyCharm
"""
# 消费者代码：rabbitmq_customer.py
import pika

# 链接到rabbitmq服务器
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
# 创建频道，声明消息队列
channel = connection.channel()
channel.queue_declare(queue='woniu')


# 定义接受消息的回调函数
def callback(ch, method, properties, body):
    print(body)


# 告诉RabbitMQ使用callback来接收信息
channel.basic_consume(on_message_callback=callback, queue='woniu', auto_ack=True)
# 开始接收信息
channel.start_consuming()

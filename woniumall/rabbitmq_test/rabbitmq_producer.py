"""
    @Time    : 2020/9/1 11:20 
    @Author  : fate
    @Site    : 
    @File    : rabbitmq_producer.py.py
    @Software: PyCharm
"""
# 生产者代码：rabbitmq_producer.py
import pika

# 链接到RabbitMQ服务器
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
# 创建频道
channel = connection.channel()
# 声明消息队列
channel.queue_declare(queue='woniu')
# routing_key是队列名 body是要插入的内容
channel.basic_publish(exchange='', routing_key='woniu', body='Hello RabbitMQ!')
print("开始向 'zxc' 队列中发布消息 'Hello RabbitMQ!'")
# 关闭链接
connection.close()

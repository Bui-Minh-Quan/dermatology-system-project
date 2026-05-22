from redis import Redis 
from rq import Queue

redis_conn = Redis(host='localhost', port=6379)

diagnosis_queue = Queue('diagnosis', connection=redis_conn)
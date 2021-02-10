import os

# https://docs.gunicorn.org/en/stable/settings.html

port_number = 8000
bind = '0.0.0.0:{0}'.format(port_number)
proc_name = 'fyle_slack_service'

backlog = int(os.environ.get('GUNICORN_BACKLOG', 2048))
workers = int(os.environ.get('GUNICORN_NUMBER_WORKERS', 1))
timeout = int(os.environ.get('GUNICORN_WORKER_TIMEOUT', 1500))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 2))
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')

reload = True

limit_request_line = 0

spew = False

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

errorlog = '-'
accesslog = '-'
access_log_format = '%({X-Real-IP}i)s - - - %(t)s "%(r)s" "%(f)s" "%(a)s" %({X-Request-Id}i)s %(L)s %(b)s %(s)s'


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):  # noqa
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    # get traceback info
    import threading
    import sys
    import traceback
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for thread_id, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(thread_id, ""),
                                            thread_id))
        for filename, line_no, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                                                        line_no, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

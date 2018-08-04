from . import server


def main():
    try:
        server.run_on_server()
    except OSError:
        server.create_server()
        server.run_on_server()

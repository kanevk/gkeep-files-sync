from . import sync_server

def main(args=None):
    print("Starting GKeep Sync Server...")

    sync_server.start_server()


if __name__ == "__main__":
    main()

# gkeep-files-sync

- Helps you backup your local file notes
- Helps you access your _Google Keep_ notes through the local file system and therefore your favorite text editor

## Setup

1. Create a label named `autosync` through the Google Keep UI

2. Clone the repo

```shell
git clone git@github.com:kanevk/gkeep-files-sync.git
cd gkeep-files-sync
```

3. Open virtual environment

```shell
pipenv shell
```

4. Install dependencies

```shell
pipenv install
```

5. Create a local config:

```shell
python3 gkeep_sync/generate_config.py "[Google email]" "[Google app password]" "[Notes root directory]"
```

\_For more information about the config options check [.config.example.json](.config.example.json)

7. Start the server

```shell
python3 gkeep_sync/sync_server.py
```

**Note:** Sometimes Google don't let you use your user password and in this case you have to fill `.config.json` field password with newly generated [App password](https://support.google.com/accounts/answer/185833?hl=en)

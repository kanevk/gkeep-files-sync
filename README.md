# gkeep-files-sync

- Helps you backup your local file notes
- Helps you easier access your Google Keep notes through your favorite text editor

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

5. Create a local config and fill it down

```shell
cp .config.example.json .config.json
```

6. Update the config with the master token

```shell
python3 generate_token.py
```

7. Start the server

```shell
python3 sync_server.py
```

**Note:** Sometimes Google don't let you use your user password and
in this case you have to fill `.config.json` field password with newly generated [App password](https://support.google.com/accounts/answer/185833?hl=en)

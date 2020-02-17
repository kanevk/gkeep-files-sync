# gkeep-files-sync

This package provides an access to your Google Keep notes under your local file system.

_Works on >=3.6 Python version._

_Not tested under Windows_

## Boring stuff

1. Go to Google Keep UI and create a label named `autosync`
2. Create a [Google App password](https://support.google.com/accounts/answer/185833?hl=en)
   - You'll be asked for a App name and you can choose any, e.g `gkeep-sync`
   - Remember this password, you'll need it later

## Install

Install the package under your OS user:

```shell
pip3 install --user gkeep-sync
```

## Run

Setup the config:

```shell
gkeep_update_config  "[Google email]" "[Google app password]" "[Notes root directory]"
```

_For more information about the config options check `.config.example.json`_

Run the server:

```shell
gkeep_sync
```

## Repo setup

Clone the repo:

```shell
git clone git@github.com:kanevk/gkeep-files-sync.git
cd gkeep-files-sync
```

Open virtual environment:

```shell
pipenv shell
```

Install dependencies:

```shell
pipenv install
```

Install the package in Develop mode into the virtual env:

```shell
pip install -e .
```

To start the server check the [section above](##Run).

**Cheers 🍺**

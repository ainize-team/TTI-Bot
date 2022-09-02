# TTI-Bot

[![Github Contributors](https://img.shields.io/github/contributors/ainize-team/TTI-Bot)](https://github.com/badges/ainize-team/TTI-Bot/contributors)
[![GitHub issues](https://img.shields.io/github/issues/ainize-team/TTI-Bot.svg)](https://github.com/ainize-team/TTI-Bot/issues)
![Github Last Commit](https://img.shields.io/github/last-commit/ainize-team/TTI-Bot)
![Github Repository Size](https://img.shields.io/github/repo-size/ainize-team/TTI-Bot)
[![GitHub Stars](https://img.shields.io/github/stars/ainize-team/TTI-Bot.svg)](https://github.com/ainize-team/TTI-Bot/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/ainize-team/TTI-Bot.svg)](https://github.com/ainize-team/TTI-Bot/network/members)
[![GitHub Watch](https://img.shields.io/github/watchers/ainize-team/TTI-Bot.svg)](https://github.com/ainize-team/TTI-Bot/watchers)

![Supported Python versions](https://img.shields.io/badge/python-3.8-brightgreen)
[![Imports](https://img.shields.io/badge/imports-isort-brightgreen)](https://pycqa.github.io/isort/)
[![Code style](https://img.shields.io/badge/code%20style-black-black)](https://black.readthedocs.io/en/stable/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
![Package Management](https://img.shields.io/badge/package%20management-poetry-blue)

## Description
Text To Image Discord Bot For AIN Dao.

## Installation
1. Build Docker Image
```
git clone https://github.com/ainize-team/TTI-Bot
cd TTI-Bot
docker build -t tti-bot .
```
2. Run Docker Image
```
docker run --name tti-bot \
     -e DISCORD_BOT_TOKEN={discord_bot_token} \
     -e DISCORD_GUILD_ID={discord_guild_id} \
     -e MODEL_ENDPOINT={model_endpoint} \
     tti-bot
```

## License

[![Licence](https://img.shields.io/github/license/ainize-team/TTI-Bot.svg)](./LICENSE)
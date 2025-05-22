# Geralt - Da Bot of Rivia

<img src = "misc\banner.png">

---
<a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-316192?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10.5">
    </a>
<a href="https://www.postgresql.org/">
    <img src="https://img.shields.io/badge/-PostgreSQL-0D1117?style=for-the-badge&logo=postgresql&labelColor=0D1117" alt="PostgreSQL 14.1">
    </a>
<a href="https://black.readthedocs.io/">
    <img src="https://img.shields.io/badge/Black-000000?style=for-the-badge&logo=&logoColor=blue" alt="Black">
    </a>

## Brief

A simple discord bot based on [**discord.py**](https://github.com/Rapptz/discord.py/) API Wrapper. Named after the legendary protagonist [**Geralt of Rivia**](https://witcher.fandom.com/wiki/Geralt_of_Rivia#:~:text=Geralt%20of%20Rivia%20was%20a%20legendary%20witcher%20of,tumultuous%20relationship%2C%20and%20became%20Ciri%20%27s%20adoptive%20father.). However, there are no commands related to the game or the series and the name for this bot came as I have a fond for the game and Geralt.

## Documentation

The website provides full details from A to Z regarding the bot. [**Click here**](https://bsod2528.github.io/pages/projects/geralt.html) to access it. All the commands, how to use them, how to setup the bot, etc. have been documented.

## Setup

An `.env` file has to be there for storing the keys. An `example_config.env` has been provided for reference. You can use any other method too like a json lmao. Just saying. Set up a venv too.

Ensure all tables are present in your [**postgresql**](https://www.postgresql.org/download/) server. Check out `db` file and use that to restore the database, as it is a backup file of the etnire database.
```py
pip install -r requirements.txt
```
Run the above command to install the packages you need for running Geralt's instance.

//setup modules
const { Client, Intents } = require('discord.js');
const { token } = require('./config.json');

//instance created 
const client = new Client({ intents: [Intents.FLAGS.GUILDS]});

//ready event
client.once('ready', () => {
    console.log('Geralt is ready fo Action!');
});

//login
client.login(token);
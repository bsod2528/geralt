const { Client, Intents } = require('discord.js');
const { token } = require('./json.json');

const Client = new Client({ intents : [Intents.FLAGS.GUILDS]});

client.once('ready', () => {
    console.log('Geralt is ready for action!');
});

client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const { commandName } = interaction;
    
    if (commandName === 'ping') {
        await interaction.reply('Pingly Pongly POOOOO! ${user}');
    }
    else if (commandName === 'server') {
        await interaction.reply('${user} The server info is below\n `Server Name : ${interaction.guild.name}\n Total no. Members : ${interaction.guild.memberCount`');
    }
    else if (commandName === 'user') {
        await interaction.reply('${user} Your info is below\n `Username : ${interaction.user.tag}\n ID : ${interaction.user.id}`');
    }
});

client.login(token);
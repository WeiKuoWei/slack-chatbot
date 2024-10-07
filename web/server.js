require('web-streams-polyfill/ponyfill');
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const moment = require('moment-timezone');
const path = require('path');
const fs = require('fs');
const { Client, GatewayIntentBits, ChannelType } = require('discord.js');

const app = express();
app.use(cors({
  origin: '*', // This is broad; consider restricting to specific origins for production
  methods: ['GET', 'POST'],
}));

app.use(express.json());
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}));

function isValidDate(dateString) {
  return moment(dateString, moment.ISO_8601, true).isValid();
}

app.get('/api/messages', async (req, res) => {
  const { guild, channel, start, end, parts } = req.query;

  if (!guild || !channel) {
    return res.status(400).send({
      message: 'Guild and Channel are required'
    });
  }

  if (!isValidDate(start) || !isValidDate(end)) {
    return res.status(400).send({
      message: 'Invalid date format'
    });
  }

  const startTime = moment(start).valueOf();
  const endTime = moment(end).valueOf();
  const numberOfParts = parseInt(parts) || 10; // default to 10 parts
  const interval = Math.floor((endTime - startTime) / numberOfParts);

  try {
    const filePath = path.join(__dirname, 'frontend/src/message_logs', guild, channel, 'message_log.json');
    if (fs.existsSync(filePath)) {
      const logData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      const filteredMessages = logData.filter(msg => {
        const msgTime = moment(msg.timestamp).valueOf();
        return msgTime >= startTime && msgTime <= endTime;
      });

      const aggregatedMessages = Array.from({ length: numberOfParts }, (_, i) => {
        const startBucket = startTime + i * interval;
        const endBucket = startBucket + interval;
        return {
          timestamp: new Date(startBucket).toISOString(),
          messages: filteredMessages.filter(msg => {
            const msgTime = moment(msg.timestamp).valueOf();
            return msgTime >= startBucket && msgTime < endBucket;
          })
        };
      });

      res.json(aggregatedMessages);
    } else {
      res.status(404).send({
        message: 'Message log not found for the specified guild and channel'
      });
    }
  } catch (error) {
    console.error('Error fetching message logs:', error);
    res.status(500).send('Failed to fetch message logs.');
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Discord Bot Code
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// Base directory for logging
const baseLogDir = path.join(__dirname, 'frontend/src/message_logs');
const archivedLogDir = path.join(__dirname, 'frontend/src/archived');
const guildMappingFile = path.join(baseLogDir, 'guild_mapping.json');
const channelMappingFile = path.join(baseLogDir, 'channel_mapping.json');

// Ensure base directory exists
function ensureBaseDir() {
  if (fs.existsSync(baseLogDir)) {
    const timestamp = moment().format('YYYYMMDD_HHmmss');
    const newArchivedDir = path.join(archivedLogDir, `message_logs_${timestamp}`);
    if (!fs.existsSync(archivedLogDir)) {
      fs.mkdirSync(archivedLogDir, { recursive: true });
    }
    fs.renameSync(baseLogDir, newArchivedDir);
    console.log(`Existing message_logs moved to: ${newArchivedDir}`);
  }
  fs.mkdirSync(baseLogDir, { recursive: true });
}

ensureBaseDir();

// Function to load mappings from a JSON file
function loadMapping(filePath) {
  if (fs.existsSync(filePath)) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  }
  return {};
}

// Function to save mappings to a JSON file
function saveMapping(filePath, mapping) {
  fs.writeFileSync(filePath, JSON.stringify(mapping, null, 4), 'utf8');
}

// Load existing mappings
const guildMapping = loadMapping(guildMappingFile);
const channelMapping = loadMapping(channelMappingFile);

// Function to ensure the directory exists
function ensureDir(filePath) {
  if (!fs.existsSync(filePath)) {
    fs.mkdirSync(filePath, { recursive: true });
  }
}

// Function to load existing messages from the JSON file
function loadMessages(guildId, channelId) {
  const filePath = path.join(baseLogDir, guildId.toString(), channelId.toString(), 'message_log.json');
  if (fs.existsSync(filePath)) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  }
  return [];
}

// Function to save messages to the JSON file
function saveMessages(guildId, channelId, messages) {
  const filePath = path.join(baseLogDir, guildId.toString(), channelId.toString(), 'message_log.json');
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(messages, null, 4), 'utf8');
}

// Function to log a message
function logMessage(message, messages) {
  if (message.author.bot) {
    return; // Ignore messages from bots
  }

  const messageData = {
    author: message.author.tag,
    author_id: message.author.id,
    content: message.content,
    timestamp: message.createdTimestamp,
    channel: message.channel.name,
    channel_id: message.channel.id,
    guild: message.guild.name,
    guild_id: message.guild.id
  };

  messages.push(messageData);
}

client.once('ready', async () => {
  console.log(`Logged in as ${client.user.tag}!`);

  // Fetch and log previous messages
  for (const guild of client.guilds.cache.values()) {
    guildMapping[guild.id] = guild.name;
    saveMapping(guildMappingFile, guildMapping);

    const channels = await guild.channels.fetch();
    for (const channel of channels.filter(c => c.type === ChannelType.GuildText).values()) {
      channelMapping[channel.id] = {
        channel_name: channel.name,
        guild_id: guild.id,
        guild_name: guild.name
      };
      try {
        let messages = loadMessages(guild.id, channel.id);
        const fetchedMessages = await channel.messages.fetch({ limit: 100 });
        fetchedMessages.forEach(message => logMessage(message, messages));
        saveMessages(guild.id, channel.id, messages);
      } catch (error) {
        console.log(`Bot does not have access to the channel: ${channel.name}`);
      }
    }
    saveMapping(channelMappingFile, channelMapping);
  }
});

client.on('messageCreate', (message) => {
  const guildId = message.guild.id;
  const channelId = message.channel.id;

  // Update mappings
  guildMapping[guildId] = message.guild.name;
  channelMapping[channelId] = {
    channel_name: message.channel.name,
    guild_id: guildId,
    guild_name: message.guild.name
  };

  saveMapping(guildMappingFile, guildMapping);
  saveMapping(channelMappingFile, channelMapping);

  // Log message
  let messages = loadMessages(guildId, channelId);
  logMessage(message, messages);
  saveMessages(guildId, channelId, messages);
});

client.login('YOUR_API_KEY');


import React, { useState, useEffect } from 'react';
import MessageGraph from './MessageGraph';
import moment from 'moment';
import './App.css';
import ChatBox from './ChatBox';
import axios from 'axios';

function App() {
  const [guildChannelState, setGuildChannelState] = useState([
    {
      guild: '', 
      channel: '', 
      channel_name: '',
      startDate: moment().subtract(1, 'days').format('YYYY-MM-DDTHH:mm'), 
      endDate: moment().format('YYYY-MM-DDTHH:mm'), 
    }
  ]);
  const [guildsChannels, setGuildsChannels] = useState({});
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');

  useEffect(() => {
    const fetchGuildsChannels = async () => {
      try {
        console.log('Fetching guilds and channels...');
        const res = await axios.get('http://localhost:8000/guilds_and_channels');
        console.log('Fetched guilds and channels:', res.data);

        if (res.data && res.data.main && res.data.main.channels) {
          setGuildsChannels(res.data);
        } else {
          console.error('Unexpected response structure:', res.data);
        }
      } catch (error) {
        console.error('Error fetching guilds and channels:', error);
      }
    };
    fetchGuildsChannels();
  }, []);

  const handleAddSelection = () => {
    setGuildChannelState([
      ...guildChannelState,
      {
        guild: '', 
        channel: '', 
        channel_name: '', 
        startDate: moment().subtract(1, 'days').format('YYYY-MM-DDTHH:mm'), 
        endDate: moment().format('YYYY-MM-DDTHH:mm'), 
      }
    ]);
  };

  const handleRemoveSelection = (index) => {
    setGuildChannelState(guildChannelState.filter((_, i) => i !== index));
  };

  const handleChange = (index, field, value) => {
    const newSelections = [...guildChannelState];
    newSelections[index][field] = value;
    if (field === 'guild') {
      newSelections[index]['channel'] = ''; // Reset channel when guild changes
      newSelections[index]['channel_name'] = '';
    }
    if (field === 'channel') {
      const selectedGuild = newSelections[index].guild;
      const selectedChannel = value;
      const channelName = getChannelNameById(selectedGuild, selectedChannel);
      newSelections[index]['channel_name'] = channelName;
    }
    setGuildChannelState(newSelections);
    console.log(`Updated selection: ${JSON.stringify(newSelections)}`); // Log updated selection
  };

  const getChannelNameById = (guildId, channelId) => {
    const channels = getChannelsByGuild(guildId);
    const channel = channels.find(channel => channel.channel_id === channelId);
    return channel ? channel.channel_name : '';
  };

  const setEndDate = (index, value) => {
    const newSelections = [...guildChannelState];
    if (moment(value).isSameOrBefore(moment(newSelections[index].startDate))) {
      newSelections[index].endDate = moment(newSelections[index].startDate).add(1, 'minutes').format('YYYY-MM-DDTHH:mm');
    } else {
      newSelections[index].endDate = value;
    }
    setGuildChannelState(newSelections);
  };

  const handleQuerySubmit = async () => {
    const selection = guildChannelState[0];
    try {
      const response = await axios.post('http://localhost:8000/query_time_period', {
        channel_id: selection.channel,
        start_time: selection.startDate,
        end_time: selection.endDate,
      });
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error querying the chat history:', error);
    }
  };

  useEffect(() => {
    if (guildChannelState[0].channel) {
      handleQuerySubmit();
    }
  }, [guildChannelState[0].channel, guildChannelState[0].startDate, guildChannelState[0].endDate]);

  const getChannelsByGuild = (guildId) => {
    const channels = guildsChannels[guildId]?.channels || [];
    console.log(`Channels for guild ${guildId}: ${JSON.stringify(channels)}`); // Log channels for the selected guild
    return channels;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Message Log Viewer</h1>
        <p>Author: Kaiwen Guo</p>
      </header>
      <div className="main-content">
        <div className="left-half">
          {guildChannelState.map((selection, index) => (
            <div key={index} style={{ borderBottom: '2px solid #ccc', paddingBottom: '20px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                <span style={{ fontSize: '24px', marginRight: '10px' }}>Guild: {selection.guild}</span>
                <span style={{ margin: '0 10px' }}> / </span>
                <span style={{ fontSize: '24px', marginRight: '10px' }}>Channel: {selection.channel_name}</span>
              </div>
              <div>
                <label>Guild: </label>
                <select
                  value={selection.guild}
                  onChange={e => handleChange(index, 'guild', e.target.value)}
                >
                  <option value="">Select Guild</option>
                  {Object.entries(guildsChannels).map(([guildId, guildData]) => (
                    <option key={guildId} value={guildId}>{`${guildData.guild_name} (${guildId})`}</option>
                  ))}
                </select>
                <label>Channel: </label>
                <select
                  value={selection.channel}
                  onChange={e => handleChange(index, 'channel', e.target.value)}
                  disabled={!selection.guild}
                >
                  <option value="">Select Channel</option>
                  {selection.guild && getChannelsByGuild(selection.guild).map(channel => (
                    <option key={channel.channel_id} value={channel.channel_id}>{`${channel.channel_name} (${channel.channel_id})`}</option>
                  ))}
                </select>
                <button onClick={() => handleRemoveSelection(index)}>Remove</button>
              </div>
              <div>
                <label>Start Date: </label>
                <input 
                  type="datetime-local" 
                  value={selection.startDate} 
                  onChange={e => handleChange(index, 'startDate', e.target.value)} 
                  max={moment(selection.endDate).subtract(1, 'minutes').format('YYYY-MM-DDTHH:mm')}
                />
                <label>End Date: </label>
                <input 
                  type="datetime-local" 
                  value={selection.endDate} 
                  onChange={e => handleChange(index, 'endDate', e.target.value)} 
                  max={moment().format('YYYY-MM-DDTHH:mm')}
                  min={moment(selection.startDate).add(1, 'minutes').format('YYYY-MM-DDTHH:mm')}
                />
              </div>
              <MessageGraph
                guild={selection.guild}
                channel={selection.channel}
                startDate={selection.startDate}
                endDate={selection.endDate}
                setEndDate={(value) => setEndDate(index, value)}
                messages={messages} // Pass the messages to MessageGraph
              />
            </div>
          ))}
          <button onClick={handleAddSelection}>Add Guild/Channel</button>
        </div>
        <div className="right-half">
          <ChatBox onRestart={() => {}} guildsChannels={guildsChannels} />
          <div>
            <h2>Messages</h2>
            <pre>{JSON.stringify(messages, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;


import React, { useState } from 'react';
import MessageGraph from './MessageGraph';
import moment from 'moment';
import './App.css';
import ChatBox from './ChatBox';
import channelMapping from './message_logs/channel_mapping.json';
import guildMapping from './message_logs/guild_mapping.json';

function App() {
  const [guildChannelState, setGuildChannelState] = useState([
    {
      guild: '', 
      channel: '', 
      startDate: moment().subtract(1, 'days').format('YYYY-MM-DDTHH:mm'), 
      endDate: moment().format('YYYY-MM-DDTHH:mm'), 
    }
  ]);

  const handleAddSelection = () => {
    setGuildChannelState([
      ...guildChannelState,
      {
        guild: '', 
        channel: '', 
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
    setGuildChannelState(newSelections);
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

  const getChannelsByGuild = (guildId) => {
    return Object.entries(channelMapping).filter(([channelId, { guild_id }]) => guild_id === guildId);
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
                <span style={{ fontSize: '24px', marginRight: '10px' }}>Channel: {selection.channel}</span>
              </div>
              <div>
                <label>Guild: </label>
                <select
                  value={selection.guild}
                  onChange={e => handleChange(index, 'guild', e.target.value)}
                >
                  <option value="">Select Guild</option>
                  {Object.entries(guildMapping).map(([guildId, guildName]) => (
                    <option key={guildId} value={guildId}>{`${guildName} (${guildId})`}</option>
                  ))}
                </select>
                <label>Channel: </label>
                <select
                  value={selection.channel}
                  onChange={e => handleChange(index, 'channel', e.target.value)}
                  disabled={!selection.guild}
                >
                  <option value="">Select Channel</option>
                  {selection.guild && getChannelsByGuild(selection.guild).map(([channelId, channelInfo]) => (
                    <option key={channelId} value={channelId}>{`${channelInfo.channel_name} (${channelId})`}</option>
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
              />
            </div>
          ))}
          <button onClick={handleAddSelection}>Add Guild/Channel</button>
        </div>
        <div className="right-half">
          <ChatBox onRestart={() => {}} />
        </div>
      </div>
    </div>
  );
}

export default App;

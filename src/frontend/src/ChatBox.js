// // // import React, { useState } from 'react';
// // // import './ChatBox.css';

// // // const ChatBox = ({ onRestart }) => {
// // //   const [messages, setMessages] = useState([]);
// // //   const [inputValue, setInputValue] = useState('');

// // //   const handleSend = () => {
// // //     if (inputValue.trim() === '') return;
// // //     setMessages([...messages, { text: inputValue, sender: 'user' }]);
// // //     setInputValue(''); // Clear the input field
// // //     // Simulate an AI response
// // //     setTimeout(() => {
// // //       setMessages(prevMessages => [...prevMessages, { text: 'This is a response from FAMS AI', sender: 'gpt' }]);
// // //     }, 1000);
// // //   };

// // //   const handleRestart = () => {
// // //     setMessages([]);
// // //     if (onRestart) onRestart();
// // //   };

// // //   return (
// // //     <div className="chat-box-container">
// // //       <div className="chat-box-header">
// // //         <h2>Chat with FAMS AI</h2>
// // //         <button className="chat-box-restart" onClick={handleRestart}>Restart</button>
// // //       </div>
// // //       <div className="chat-box-messages">
// // //         {messages.map((message, index) => (
// // //           <div key={index} className={`chat-box-message ${message.sender}`}>
// // //             <span className="sender-label">{message.sender === 'user' ? 'User' : 'FAMS AI'}: </span>
// // //             {message.text}
// // //           </div>
// // //         ))}
// // //       </div>
// // //       <div className="chat-box-input-container">
// // //         <input 
// // //           type="text" 
// // //           className="chat-box-input" 
// // //           value={inputValue}
// // //           onChange={(e) => setInputValue(e.target.value)}
// // //           onKeyDown={(e) => e.key === 'Enter' && handleSend()}
// // //           placeholder="Type your message..."
// // //         />
// // //         <button className="chat-box-button" onClick={handleSend}>Send</button>
// // //       </div>
// // //     </div>
// // //   );
// // // };

// // // export default ChatBox;
// // import React, { useState, useEffect } from 'react';
// // import './ChatBox.css';
// // import axios from 'axios';

// // const ChatBox = ({ onRestart, guildsChannels }) => {
// //   const [messages, setMessages] = useState([]);
// //   const [inputValue, setInputValue] = useState('');
// //   const [selectedGuild, setSelectedGuild] = useState('');
// //   const [selectedChannel, setSelectedChannel] = useState('');
// //   const [channelName, setChannelName] = useState('');

// //   useEffect(() => {
// //     if (selectedGuild && selectedChannel) {
// //       const channels = guildsChannels[selectedGuild]?.channels || [];
// //       const channel = channels.find(channel => channel.channel_id === selectedChannel);
// //       setChannelName(channel ? channel.channel_name : '');
// //     }
// //   }, [selectedGuild, selectedChannel, guildsChannels]);

// //   const handleSend = async () => {
// //     if (inputValue.trim() === '' || !selectedGuild || !selectedChannel) return;

// //     setMessages([...messages, { text: inputValue, sender: 'user' }]);
// //     setInputValue(''); // Clear the input field

// //     try {
// //       const response = await axios.post('http://localhost:8000/general', {
// //         guild_id: selectedGuild,
// //         channel_id: selectedChannel,
// //         query: inputValue,
// //       });
// //       const answer = response.data.answer;
// //       setMessages(prevMessages => [...prevMessages, { text: answer, sender: 'gpt' }]);
// //     } catch (error) {
// //       console.error('Error fetching GPT response:', error);
// //       setMessages(prevMessages => [...prevMessages, { text: 'Error fetching response from FAMS AI', sender: 'gpt' }]);
// //     }
// //   };

// //   const handleRestart = () => {
// //     setMessages([]);
// //     if (onRestart) onRestart();
// //   };

// //   return (
// //     <div className="chat-box-container">
// //       <div className="chat-box-header">
// //         <h2>Chat with FAMS AI</h2>
// //         <button className="chat-box-restart" onClick={handleRestart}>Restart</button>
// //       </div>
// //       <div className="chat-box-selection">
// //         <label>Guild: </label>
// //         <select
// //           value={selectedGuild}
// //           onChange={e => {
// //             setSelectedGuild(e.target.value);
// //             setSelectedChannel(''); // Reset channel when guild changes
// //           }}
// //         >
// //           <option value="">Select Guild</option>
// //           {Object.entries(guildsChannels).map(([guildId, guildData]) => (
// //             <option key={guildId} value={guildId}>{`${guildData.guild_name} (${guildId})`}</option>
// //           ))}
// //         </select>
// //         <label>Channel: </label>
// //         <select
// //           value={selectedChannel}
// //           onChange={e => setSelectedChannel(e.target.value)}
// //           disabled={!selectedGuild}
// //         >
// //           <option value="">Select Channel</option>
// //           {selectedGuild && guildsChannels[selectedGuild]?.channels.map(channel => (
// //             <option key={channel.channel_id} value={channel.channel_id}>{`${channel.channel_name} (${channel.channel_id})`}</option>
// //           ))}
// //         </select>
// //       </div>
// //       <div className="chat-box-messages">
// //         {messages.map((message, index) => (
// //           <div key={index} className={`chat-box-message ${message.sender}`}>
// //             <span className="sender-label">{message.sender === 'user' ? 'User' : 'FAMS AI'}: </span>
// //             {message.text}
// //           </div>
// //         ))}
// //       </div>
// //       <div className="chat-box-input-container">
// //         <input 
// //           type="text" 
// //           className="chat-box-input" 
// //           value={inputValue}
// //           onChange={(e) => setInputValue(e.target.value)}
// //           onKeyDown={(e) => e.key === 'Enter' && handleSend()}
// //           placeholder="Type your message..."
// //         />
// //         <button className="chat-box-button" onClick={handleSend}>Send</button>
// //       </div>
// //     </div>
// //   );
// // };

// // export default ChatBox;
// import React, { useState, useEffect } from 'react';
// import './ChatBox.css';
// import axios from 'axios';

// const ChatBox = ({ onRestart, guildsChannels }) => {
//   const [messages, setMessages] = useState([]);
//   const [inputValue, setInputValue] = useState('');
//   const [selectedGuild, setSelectedGuild] = useState('');
//   const [selectedChannel, setSelectedChannel] = useState('');
//   const [channelName, setChannelName] = useState('');

//   useEffect(() => {
//     if (selectedGuild && selectedChannel) {
//       const channels = guildsChannels[selectedGuild]?.channels || [];
//       const channel = channels.find(channel => channel.channel_id === selectedChannel);
//       setChannelName(channel ? channel.channel_name : '');
//     }
//   }, [selectedGuild, selectedChannel, guildsChannels]);

//   const handleSend = async () => {
//     if (inputValue.trim() === '' || !selectedGuild || !selectedChannel) return;
  
//     setMessages([...messages, { text: inputValue, sender: 'user' }]);
//     setInputValue(''); // Clear the input field
  
//     const payload = {
//       guild_id: selectedGuild,
//       channel_id: selectedChannel,
//       query: inputValue,
//     };
  
//     console.log('Sending payload:', payload);
  
//     try {
//       const response = await axios.post('http://localhost:8000/general', payload);
//       const answer = response.data.answer;
//       setMessages(prevMessages => [...prevMessages, { text: answer, sender: 'gpt' }]);
//     } catch (error) {
//       console.error('Error fetching GPT response:', error);
//       setMessages(prevMessages => [...prevMessages, { text: 'Error fetching response from FAMS AI', sender: 'gpt' }]);
//     }
//   };
  

//   const handleRestart = () => {
//     setMessages([]);
//     if (onRestart) onRestart();
//   };

//   return (
//     <div className="chat-box-container">
//       <div className="chat-box-header">
//         <h2>Chat with FAMS AI</h2>
//         <button className="chat-box-restart" onClick={handleRestart}>Restart</button>
//       </div>
//       <div className="chat-box-selection">
//         <label>Guild: </label>
//         <select
//           value={selectedGuild}
//           onChange={e => {
//             setSelectedGuild(e.target.value);
//             setSelectedChannel(''); // Reset channel when guild changes
//           }}
//         >
//           <option value="">Select Guild</option>
//           {Object.entries(guildsChannels).map(([guildId, guildData]) => (
//             <option key={guildId} value={guildId}>{`${guildData.guild_name} (${guildId})`}</option>
//           ))}
//         </select>
//         <label>Channel: </label>
//         <select
//           value={selectedChannel}
//           onChange={e => setSelectedChannel(e.target.value)}
//           disabled={!selectedGuild}
//         >
//           <option value="">Select Channel</option>
//           {selectedGuild && guildsChannels[selectedGuild]?.channels.map(channel => (
//             <option key={channel.channel_id} value={channel.channel_id}>{`${channel.channel_name} (${channel.channel_id})`}</option>
//           ))}
//         </select>
//       </div>
//       <div className="chat-box-messages">
//         {messages.map((message, index) => (
//           <div key={index} className={`chat-box-message ${message.sender}`}>
//             <span className="sender-label">{message.sender === 'user' ? 'User' : 'FAMS AI'}: </span>
//             {message.text}
//           </div>
//         ))}
//       </div>
//       <div className="chat-box-input-container">
//         <input 
//           type="text" 
//           className="chat-box-input" 
//           value={inputValue}
//           onChange={(e) => setInputValue(e.target.value)}
//           onKeyDown={(e) => e.key === 'Enter' && handleSend()}
//           placeholder="Type your message..."
//         />
//         <button className="chat-box-button" onClick={handleSend}>Send</button>
//       </div>
//     </div>
//   );
// };

// export default ChatBox;
import React, { useState, useEffect } from 'react';
import './ChatBox.css';
import axios from 'axios';

const ChatBox = ({ onRestart, guildsChannels }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedGuild, setSelectedGuild] = useState('');
  const [selectedChannel, setSelectedChannel] = useState('');
  const [channelName, setChannelName] = useState('');

  useEffect(() => {
    if (selectedGuild && selectedChannel) {
      const channels = guildsChannels[selectedGuild]?.channels || [];
      const channel = channels.find(channel => channel.channel_id === selectedChannel);
      setChannelName(channel ? channel.channel_name : '');
    }
  }, [selectedGuild, selectedChannel, guildsChannels]);

  const handleSend = async () => {
    if (inputValue.trim() === '' || !selectedGuild || !selectedChannel) return;

    setMessages([...messages, { text: inputValue, sender: 'user' }]);
    setInputValue(''); // Clear the input field

    const payload = {
      // guild_id: parseInt(selectedGuild, 10),
      guild_id: 1,
      channel_id: selectedChannel,
      query: inputValue,
    };

    console.log('Sending payload:', payload); // Add this line to print the payload

    try {
      const response = await axios.post('http://localhost:8000/super', payload);
      const answer = response.data.answer;
      setMessages(prevMessages => [...prevMessages, { text: answer, sender: 'gpt' }]);
    } catch (error) {
      console.error('Error fetching GPT response:', error);
      setMessages(prevMessages => [...prevMessages, { text: 'Error fetching response from FAMS AI', sender: 'gpt' }]);
    }
  };

  const handleRestart = () => {
    setMessages([]);
    if (onRestart) onRestart();
  };

  return (
    <div className="chat-box-container">
      <div className="chat-box-header">
        <h2>Chat with FAMS AI</h2>
        <button className="chat-box-restart" onClick={handleRestart}>Restart</button>
      </div>
      <div className="chat-box-selection">
        <label>Guild: </label>
        <select
          value={selectedGuild}
          onChange={e => {
            setSelectedGuild(e.target.value);
            setSelectedChannel(''); // Reset channel when guild changes
          }}
        >
          <option value="">Select Guild</option>
          {Object.entries(guildsChannels).map(([guildId, guildData]) => (
            <option key={guildId} value={guildId}>{`${guildData.guild_name} (${guildId})`}</option>
          ))}
        </select>
        <label>Channel: </label>
        <select
          value={selectedChannel}
          onChange={e => setSelectedChannel(e.target.value)}
          disabled={!selectedGuild}
        >
          <option value="">Select Channel</option>
          {selectedGuild && guildsChannels[selectedGuild]?.channels.map(channel => (
            <option key={channel.channel_id} value={channel.channel_id}>{`${channel.channel_name} (${channel.channel_id})`}</option>
          ))}
        </select>
      </div>
      <div className="chat-box-messages">
        {messages.map((message, index) => (
          <div key={index} className={`chat-box-message ${message.sender}`}>
            <span className="sender-label">{message.sender === 'user' ? 'User' : 'FAMS AI'}: </span>
            {message.text}
          </div>
        ))}
      </div>
      <div className="chat-box-input-container">
        <input 
          type="text" 
          className="chat-box-input" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
        />
        <button className="chat-box-button" onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default ChatBox;


import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import Modal from 'react-modal';
import moment from 'moment-timezone';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

Modal.setAppElement('#root'); // To avoid screen reader issues

const MessageGraph = ({ guild, channel, startDate, endDate, setEndDate, messages }) => {
  const [data, setData] = useState({
    labels: [],
    datasets: [
      {
        label: `${guild}-${channel} Messages`,
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  });
  const [error, setError] = useState('');
  const [parts, setParts] = useState(10); // default to 10 parts
  const [displayData, setDisplayData] = useState([]); // Initialize displayData state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTimePeriod, setSelectedTimePeriod] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  useEffect(() => {
    if (messages.length > 0) {
      const start = moment(startDate);
      const end = moment(endDate);
      const duration = end.diff(start) / parts; // duration of each interval in milliseconds

      const intervals = Array.from({ length: parts }, (_, i) => {
        const intervalStart = start.clone().add(i * duration, 'milliseconds');
        const intervalEnd = intervalStart.clone().add(duration, 'milliseconds');
        return { intervalStart, intervalEnd };
      });

      const messageData = intervals.map(({ intervalStart, intervalEnd }) => {
        const messagesInInterval = messages.filter(msg =>
          moment.utc(msg.timestamp).isBetween(intervalStart, intervalEnd)
        );
        return {
          x: intervalStart.local().format('YYYY-MM-DD HH:mm:ss'),
          y: messagesInInterval.length,
          messages: messagesInInterval,
        };
      });

      setData({
        labels: messageData.map(d => d.x),
        datasets: [{
          label: `${guild}-${channel} Messages`,
          data: messageData.map(d => d.y),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
        }],
      });
      setDisplayData(messageData); // Set displayData with messageData
    }
  }, [messages, guild, channel, startDate, endDate, parts]);

  const handleSetNow = () => {
    const now = moment().format('YYYY-MM-DDTHH:mm');
    setEndDate(now); // Update endDate state in parent component to now
  };

  const getUserStatistics = () => {
    return displayData.map(period => {
      const userMessageCount = period.messages.reduce((acc, msg) => {
        acc[msg.author] = (acc[msg.author] || 0) + 1;
        return acc;
      }, {});

      const mostActiveUser = Object.keys(userMessageCount).reduce((a, b) => userMessageCount[a] > userMessageCount[b] ? a : b, null);
      const nightMessages = period.messages.filter(msg => {
        const hour = moment(msg.timestamp).local().hour();
        return (hour >= 0 && hour < 6) || (hour >= 18 && hour < 24);
      }).length;
      const dayMessages = period.messages.length - nightMessages;

      return {
        timePeriod: period.x,
        totalMessages: period.y,
        mostActiveUser,
        nightMessages,
        dayMessages,
        messages: period.messages
      };
    });
  };

  const options = {
    plugins: {
      tooltip: {
        callbacks: {
          title: (context) => {
            const index = context[0].dataIndex;
            const hoveredLabel = data.labels[index];
            const intervalDuration = Math.floor((moment(endDate).valueOf() - moment(startDate).valueOf()) / parts);
            const hoveredTime = moment(hoveredLabel).local().format('YYYY-MM-DD HH:mm:ss');
            const nextTime = moment(hoveredLabel).add(intervalDuration, 'milliseconds').local().format('YYYY-MM-DD HH:mm:ss');
            return `Time Period: ${hoveredTime} to ${nextTime}`;
          },
          label: (context) => {
            return `Total Messages: ${context.raw}`;
          }
        }
      }
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedTimePeriod(null);
  };

  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
  };

  const handleTimePeriodClick = (timePeriod) => {
    setSelectedTimePeriod(timePeriod);
    setIsDetailModalOpen(true);
  };

  const renderMessages = (messages) => (
    <ul>
      {messages.map((msg, index) => (
        <li key={index}>{moment(msg.timestamp).format('YYYY-MM-DD HH:mm:ss')} - {msg.author}: {msg['chroma:document']}</li>
      ))}
    </ul>
  );

  return (
    <div>
      <div>
        <label>Granularity: </label>
        <select value={parts} onChange={e => setParts(parseInt(e.target.value))}>
          <option value={5}>5 Parts</option>
          <option value={10}>10 Parts</option>
          <option value={15}>15 Parts</option>
          <option value={20}>20 Parts</option>
          <option value={25}>25 Parts</option>
        </select>
      </div>
      <button onClick={handleSetNow}>Set End Date to Now</button>
      <button onClick={() => setIsModalOpen(true)}>Display Data</button>
      <Line data={data} options={options} />
      <Modal
        isOpen={isModalOpen}
        onRequestClose={closeModal}
        contentLabel="User Statistics"
        style={{
          content: {
            top: '50%',
            left: '50%',
            right: 'auto',
            bottom: 'auto',
            marginRight: '-50%',
            transform: 'translate(-50%, -50%)',
            maxHeight: '80vh',
            overflowY: 'auto',
          },
        }}
      >
        <div className="modal-header">
          <h2>User Statistics</h2>
          <span className="close-button" onClick={closeModal}>&times;</span>
        </div>
        <div>
          {getUserStatistics().map((stat, index) => (
            <div key={index} className="user-statistics" onClick={() => handleTimePeriodClick(stat)}>
              <h4>{stat.timePeriod}</h4>
              <p>Total Messages: {stat.totalMessages}</p>
              <p>Most Active User: {stat.mostActiveUser}</p>
              <p>Night Messages: {stat.nightMessages}</p>
              <p>Day Messages: {stat.dayMessages}</p>
            </div>
          ))}
        </div>
      </Modal>
      <Modal
        isOpen={isDetailModalOpen}
        onRequestClose={closeDetailModal}
        contentLabel="Detailed Messages"
        style={{
          content: {
            top: '50%',
            left: '50%',
            right: 'auto',
            bottom: 'auto',
            marginRight: '-50%',
            transform: 'translate(-50%, -50%)',
            maxHeight: '80vh',
            overflowY: 'auto',
          },
        }}
      >
        <div className="modal-header">
          <h2>Messages from {selectedTimePeriod?.timePeriod}</h2>
          <span className="close-button" onClick={closeDetailModal}>&times;</span>
        </div>
        {selectedTimePeriod && renderMessages(selectedTimePeriod.messages)}
      </Modal>
    </div>
  );
};

export default MessageGraph;
